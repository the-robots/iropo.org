import { TYPE_LABELS } from "../lib/format";
import type { AgencyType } from "../lib/types";

type Row = [string, string, string, string, AgencyType, number | null, number | null, string | 0];
interface Index {
  year: number;
  states: Record<string, [string, string]>;
  rows: Row[];
}

const form = document.querySelector<HTMLFormElement>("#agency-search");
const input = document.querySelector<HTMLInputElement>("#q");
const stateSelect = document.querySelector<HTMLSelectElement>("#state");
const typeSelect = document.querySelector<HTMLSelectElement>("#type");
const casesOnly = document.querySelector<HTMLInputElement>("#cases");
const results = document.querySelector<HTMLOListElement>("#results");
const status = document.querySelector<HTMLElement>("#results-status");
const defaults = document.querySelector<HTMLElement>("#default-results");

const LIMIT = 60;
let index: Index | null = null;
let haystacks: string[] = [];
let loading: Promise<Index> | null = null;

const norm = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, " ").trim();

function load(): Promise<Index> {
  loading ??= fetch("/data/agency-index.json")
    .then((r) => r.json() as Promise<Index>)
    .then((data) => {
      index = data;
      haystacks = data.rows.map((r) => ` ${norm(`${r[1]} ${r[0]} ${r[3]} ${r[2]} ${data.states[r[2]]?.[0] ?? ""}`)}`);
      return data;
    });
  return loading;
}

function score(row: Row, hay: string, terms: string[], raw: string): number {
  let s = 0;
  if (row[0] && row[0].toLowerCase() === raw.toLowerCase()) s += 1000;
  const name = ` ${norm(row[1])}`;
  if (name.startsWith(` ${terms.join(" ")}`)) s += 60;
  for (const t of terms) if (hay.includes(` ${t}`)) s += 10;
  return s + Math.log10((row[6] ?? 0) + 1) * 5;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className?: string, text?: string) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function render() {
  if (!index || !results || !status) return;
  const raw = input?.value.trim() ?? "";
  const terms = norm(raw).split(" ").filter(Boolean);
  const st = stateSelect?.value ?? "";
  const type = typeSelect?.value ?? "";
  const onlyCases = casesOnly?.checked ?? false;
  const filtering = terms.length > 0 || st || type || onlyCases;

  if (defaults) defaults.hidden = Boolean(filtering);
  results.replaceChildren();
  if (!filtering) {
    status.textContent = "";
    return;
  }

  const matches: { row: Row; s: number }[] = [];
  index.rows.forEach((row, i) => {
    if (st && row[2] !== st) return;
    if (type && row[4] !== type) return;
    if (onlyCases && !(row[6] && row[6] > 0)) return;
    const hay = haystacks[i];
    if (!terms.every((t) => hay.includes(t))) return;
    matches.push({ row, s: score(row, hay, terms, raw) });
  });
  matches.sort((a, b) => b.s - a.s || (b.row[6] ?? 0) - (a.row[6] ?? 0) || a.row[1].localeCompare(b.row[1]));

  status.textContent =
    matches.length === 0
      ? "No agencies match. Try a shorter name, a city or county, or an ORI."
      : `${matches.length.toLocaleString("en-US")} ${matches.length === 1 ? "agency" : "agencies"} found${matches.length > LIMIT ? `, showing the first ${LIMIT}` : ""}.`;

  for (const { row } of matches.slice(0, LIMIT)) {
    const [ori, name, abbr, county, t, latest, total, anchor] = row;
    const [stateName, slug] = index.states[abbr] ?? [abbr, abbr.toLowerCase()];
    const li = el("li", "result card");
    const link = el("a", "result__name", name);
    link.setAttribute("href", `/states/${slug}/agencies/#${ori || anchor}`);
    const meta = el("p", "result__meta");
    meta.append(
      el("span", "mono", ori || "No ORI"),
      el("span", undefined, TYPE_LABELS[t] ?? t),
      el("span", undefined, county ? `${county}, ${stateName}` : stateName),
    );
    const counts = el("p", "result__counts");
    if (total === null) {
      counts.textContent = "Not in FBI agency tables";
      counts.classList.add("muted");
    } else {
      counts.append(el("strong", undefined, (latest ?? 0).toLocaleString("en-US")), ` in ${index.year} · ${total.toLocaleString("en-US")} since 2020`);
    }
    li.append(link, meta, counts);
    results.append(li);
  }
}

let timer: number | undefined;
const schedule = () => {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => {
    load().then(render).catch(() => {
      if (status) status.textContent = "The agency index could not be loaded. Browse by state instead.";
    });
  }, 120);
};

if (form && input) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    schedule();
  });
  input.addEventListener("focus", () => void load(), { once: true });
  [input, stateSelect, typeSelect, casesOnly].forEach((c) => c?.addEventListener("input", schedule));
  const q = new URLSearchParams(location.search).get("q");
  if (q) {
    input.value = q;
    schedule();
  }
}
