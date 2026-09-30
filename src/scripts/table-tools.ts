/**
 * Progressive enhancement for static tables marked with [data-table-tools]:
 * text filtering, select/checkbox filters and sortable columns. Without JavaScript the full
 * table is still rendered and readable.
 *
 * Markup contract:
 *   <div data-table-tools>
 *     <input data-filter-text> <select data-filter-attr="type"> <input type="checkbox" data-filter-flag="cases">
 *     <span data-filter-status></span>
 *     <table> <th data-sort="text|num"><button>…</button></th> … <tr data-search="…" data-type="…" data-cases="1">
 */
function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function initTable(root: HTMLElement) {
  const table = root.querySelector<HTMLTableElement>("table");
  const body = table?.tBodies[0];
  if (!table || !body) return;
  const rows = Array.from(body.rows);
  const text = root.querySelector<HTMLInputElement>("[data-filter-text]");
  const selects = Array.from(root.querySelectorAll<HTMLSelectElement>("[data-filter-attr]"));
  const flags = Array.from(root.querySelectorAll<HTMLInputElement>("[data-filter-flag]"));
  const status = root.querySelector<HTMLElement>("[data-filter-status]");
  const searchIndex = new Map(rows.map((row) => [row, normalize(row.dataset.search ?? row.textContent ?? "")]));

  const apply = () => {
    const terms = normalize(text?.value ?? "").split(" ").filter(Boolean);
    let shown = 0;
    for (const row of rows) {
      const haystack = searchIndex.get(row) ?? "";
      let visible = terms.every((t) => haystack.includes(t));
      for (const select of selects) {
        const attr = select.dataset.filterAttr!;
        if (visible && select.value && row.dataset[attr] !== select.value) visible = false;
      }
      for (const flag of flags) {
        if (visible && flag.checked && row.dataset[flag.dataset.filterFlag!] !== "1") visible = false;
      }
      row.hidden = !visible;
      if (visible) shown++;
    }
    if (status) status.textContent = `Showing ${shown.toLocaleString("en-US")} of ${rows.length.toLocaleString("en-US")}`;
  };

  text?.addEventListener("input", apply);
  selects.forEach((s) => s.addEventListener("change", apply));
  flags.forEach((f) => f.addEventListener("change", apply));

  const headers = Array.from(table.tHead?.rows[0]?.cells ?? []);
  headers.forEach((th, index) => {
    const kind = th.dataset.sort;
    const button = th.querySelector("button");
    if (!kind || !button) return;
    button.addEventListener("click", () => {
      const ascending = th.getAttribute("aria-sort") !== "ascending";
      headers.forEach((h) => h.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
      const value = (row: HTMLTableRowElement) => {
        const cell = row.cells[index];
        const raw = cell?.dataset.value ?? cell?.textContent ?? "";
        if (kind === "num") {
          const n = Number(raw.replace(/[^0-9.\-]/g, ""));
          return Number.isFinite(n) && raw.trim() !== "" && raw.trim() !== "—" ? n : -Infinity;
        }
        return raw.trim().toLowerCase();
      };
      const sorted = [...body.rows].sort((a, b) => {
        const va = value(a);
        const vb = value(b);
        const cmp = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
        return ascending ? cmp : -cmp;
      });
      body.append(...sorted);
    });
  });

  const params = new URLSearchParams(location.search);
  const q = params.get("q");
  if (text && q) text.value = q;
  for (const select of selects) {
    const value = params.get(select.dataset.filterAttr!);
    if (value && [...select.options].some((o) => o.value === value)) select.value = value;
  }
  apply();
}

document.querySelectorAll<HTMLElement>("[data-table-tools]").forEach(initTable);
