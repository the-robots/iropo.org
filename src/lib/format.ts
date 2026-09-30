import type { AgencyType } from "./types";

const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

export function fmt(value: number | null | undefined, fallback = "—"): string {
  return value === null || value === undefined || Number.isNaN(value) ? fallback : integer.format(value);
}

export function fmtCompact(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : compact.format(value);
}

export function fmtRate(value: number | null | undefined, digits = 1): string {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

/** 0.302 -> "30%" (share given as a fraction). */
export function fmtShare(value: number | null | undefined, digits = 0): string {
  return value === null || value === undefined ? "—" : `${(value * 100).toFixed(digits)}%`;
}

/** 88.7 -> "89%" (value already in percent). */
export function fmtPct(value: number | null | undefined, digits = 0): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(digits)}%`;
}

export function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso.length === 10 ? `${iso}T00:00:00Z` : iso);
  return date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
}

/** "09/15/2026" (CDE format) -> "September 15, 2026". */
export function fmtCdeDate(value: string | null | undefined): string {
  if (!value) return "—";
  const [month, day, year] = value.split("/");
  if (!year) {
    const date = new Date(Date.UTC(Number(day), Number(month) - 1, 1));
    return date.toLocaleDateString("en-US", { year: "numeric", month: "long", timeZone: "UTC" });
  }
  return fmtDate(`${year}-${month}-${day}`);
}

export const TYPE_LABELS: Record<AgencyType, string> = {
  city: "City police",
  county: "County",
  university: "University or college",
  other: "Other",
  other_state: "Other state agency",
  state_police: "State police",
  tribal: "Tribal",
  federal: "Federal",
};

export const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${fmt(count)} ${count === 1 ? one : many}`;
}

export function ordinal(n: number): string {
  const suffix = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${suffix[(v - 20) % 10] || suffix[v] || suffix[0]}`;
}

/** ["a", "b", "c"] -> "a, b and c". */
export function listJoin(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}
