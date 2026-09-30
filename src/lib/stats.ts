import { agenciesFor, LATEST_TABLE_YEAR, national, officialRegistries, states } from "./data";
import type { Agency, AnnualPoint, OffenderDimension, StateSummary } from "./types";

/** Years where less than this share of the population was covered are shown as incomplete. */
export const LOW_COVERAGE_PCT = 60;

/** A latest-year rate is comparable when coverage is broad and the state is not in a reporting gap. */
export function comparable(p: AnnualPoint): boolean {
  return p.coverage_pct >= 50 && p.rate_per_100k !== null && p.rate_per_100k >= 1;
}

export function latest(annual: AnnualPoint[]): AnnualPoint {
  return annual[annual.length - 1];
}

export function point(annual: AnnualPoint[], year: number): AnnualPoint | undefined {
  return annual.find((p) => p.year === year);
}

/** First year with all 12 months reported, cases recorded, and NIBRS covering most residents. */
export function firstFullYear(annual: AnnualPoint[]): number | null {
  return annual.find((p) => p.months_reported === 12 && (p.offenses ?? 0) > 0 && p.coverage_pct >= 50)?.year ?? null;
}

export function pctChange(from: number | null | undefined, to: number | null | undefined): number | null {
  if (!from || to === null || to === undefined) return null;
  return (to - from) / from;
}

export interface RankedState {
  state: StateSummary;
  latest: AnnualPoint;
  rank: number | null;
}

/** States ranked by the latest year's rate per 100k covered residents (highest first). */
export function rankStates(minCoverage = 50): RankedState[] {
  const rows = states.map((state) => ({ state, latest: latest(state.annual) }));
  const eligible = rows
    .filter((r) => comparable(r.latest) && r.latest.coverage_pct >= minCoverage)
    .sort((a, b) => (b.latest.rate_per_100k ?? 0) - (a.latest.rate_per_100k ?? 0));
  const ranks = new Map(eligible.map((r, i) => [r.state.abbr, i + 1]));
  return rows.map((r) => ({ ...r, rank: ranks.get(r.state.abbr) ?? null }));
}

/**
 * Average offenses per day for each calendar month over the most recent `years` full years.
 * Per-day averages keep short months (February) comparable with long ones.
 */
export function seasonality(monthly: { start: string | null; offenses: (number | null)[] }, years = 4) {
  if (!monthly.start) return [];
  const startYear = Number(monthly.start.slice(0, 4));
  const startMonth = Number(monthly.start.slice(5, 7)) - 1;
  const totals = Array.from({ length: 12 }, () => ({ sum: 0, n: 0 }));
  const lastYear = startYear + Math.floor((startMonth + monthly.offenses.length - 1) / 12);
  monthly.offenses.forEach((value, i) => {
    const year = startYear + Math.floor((startMonth + i) / 12);
    const month = (startMonth + i) % 12;
    if (value === null || year <= lastYear - years) return;
    const days = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
    totals[month].sum += value / days;
    totals[month].n += 1;
  });
  return totals.map((t) => (t.n ? t.sum / t.n : 0));
}

export interface ShareRow {
  key: string;
  label: string;
  cruelty: number;
  all: number;
}

/** Shares (0-1) of known offenders in each group, excluding "unknown". */
export function shares(dimension: OffenderDimension, labels: Record<string, string>): ShareRow[] {
  const keys = Object.keys(labels);
  const known = (table: Record<string, number>) => keys.reduce((sum, k) => sum + (table[k] ?? 0), 0);
  const cTotal = known(dimension.animal_cruelty);
  const aTotal = known(dimension.all_offenses);
  return keys.map((key) => ({
    key,
    label: labels[key],
    cruelty: cTotal ? (dimension.animal_cruelty[key] ?? 0) / cTotal : 0,
    all: aTotal ? (dimension.all_offenses[key] ?? 0) / aTotal : 0,
  }));
}

export const AGE_LABELS: Record<string, string> = {
  "0-10": "10 and under",
  "11-15": "11–15",
  "16-20": "16–20",
  "21-25": "21–25",
  "26-30": "26–30",
  "31-35": "31–35",
  "36-40": "36–40",
  "41-45": "41–45",
  "46-50": "46–50",
  "51-55": "51–55",
  "56-60": "56–60",
  "61-65": "61–65",
  "66+": "66 and over",
};
export const SEX_LABELS: Record<string, string> = { male: "Male", female: "Female" };
export const RACE_LABELS: Record<string, string> = {
  white: "White",
  black: "Black or African American",
  american_indian_alaska_native: "American Indian or Alaska Native",
  asian: "Asian",
  native_hawaiian_pacific_islander: "Native Hawaiian or Other Pacific Islander",
};
export const AGE_CATEGORY_LABELS: Record<string, string> = { adult: "Adult", juvenile: "Juvenile (under 18)" };

export function latestOffenders() {
  const year = national.offenders.years[national.offenders.years.length - 1];
  return { year, tables: national.offenders.by_year[String(year)] };
}

/** Headline comparisons between animal cruelty offenders and all offenders. */
export function offenderHighlights() {
  const { year, tables } = latestOffenders();
  const sex = shares(tables.sex, SEX_LABELS);
  const age = shares(tables.age, AGE_LABELS);
  const category = shares(tables.age_category, AGE_CATEGORY_LABELS);
  const female = sex.find((r) => r.key === "female")!;
  const older = age.filter((r) => ["56-60", "61-65", "66+"].includes(r.key));
  return {
    year,
    total: tables.sex.animal_cruelty.total,
    female,
    over55: {
      cruelty: older.reduce((s, r) => s + r.cruelty, 0),
      all: older.reduce((s, r) => s + r.all, 0),
    },
    juvenile: category.find((r) => r.key === "juvenile")!,
  };
}

export function agencyTotal(agency: Agency): number {
  return Object.values(agency.animal_cruelty ?? {}).reduce<number>((sum, v) => sum + (v ?? 0), 0);
}

export function agencyLatest(agency: Agency, year = LATEST_TABLE_YEAR): number | null {
  const value = agency.animal_cruelty?.[String(year)];
  return value === undefined ? null : value;
}

export function topAgencies(abbr: string, limit = 15, year = LATEST_TABLE_YEAR): Agency[] {
  return agenciesFor(abbr)
    .agencies.filter((a) => (agencyLatest(a, year) ?? 0) > 0)
    .sort((a, b) => (agencyLatest(b, year) ?? 0) - (agencyLatest(a, year) ?? 0) || agencyTotal(b) - agencyTotal(a))
    .slice(0, limit);
}

export function registriesFor(abbr: string) {
  return officialRegistries.registries.filter((r) => r.state === abbr);
}

export interface QualityNote {
  kind: "gap" | "coverage" | "welfare" | "new";
  text: string;
}

/** Data-driven caveats that should accompany a state's latest figures. */
export function qualityNotes(state: StateSummary): QualityNote[] {
  const notes: QualityNote[] = [];
  const last = latest(state.annual);
  if (last.coverage_pct >= 50 && (last.rate_per_100k ?? 0) < 1) {
    notes.push({
      kind: "gap",
      text: `Agencies covering ${Math.round(last.coverage_pct)}% of residents reported ${last.offenses ?? 0} animal cruelty offenses in ${last.year}. That almost certainly reflects how cruelty is recorded or submitted in ${state.name}, not an absence of cruelty.`,
    });
  }
  if (last.coverage_pct < 60) {
    notes.push({
      kind: "coverage",
      text: `Only ${Math.round(last.coverage_pct)}% of ${state.name} residents were served by agencies reporting to NIBRS in ${last.year}, so statewide totals are incomplete.`,
    });
  }
  const agencies = agenciesFor(state.abbr).agencies;
  const year = String(LATEST_TABLE_YEAR);
  const total = agencies.reduce((s, a) => s + (a.animal_cruelty?.[year] ?? 0), 0);
  const welfare = agencies
    .filter((a) => /animal|humane|spca/i.test(a.name))
    .reduce((s, a) => s + (a.animal_cruelty?.[year] ?? 0), 0);
  if (total > 0 && welfare / total >= 0.25) {
    notes.push({
      kind: "welfare",
      text: `Animal welfare agencies in ${state.name} report cruelty cases directly to the FBI (${Math.round((welfare / total) * 100)}% of the ${year} total), which makes its rate much higher than states where these cases stay outside police records.`,
    });
  }
  const first = firstFullYear(state.annual);
  if (first !== null && first >= last.year - 3) {
    notes.push({
      kind: "new",
      text: `${state.name} has had broad NIBRS coverage only since ${first}, so earlier years are not comparable with later ones.`,
    });
  }
  return notes;
}

/** Sequential color bins for choropleths, light to dark. */
export const SCALE = ["#fdf0e1", "#fbd7b0", "#f7b57a", "#ef8a4b", "#d9612c", "#b1441c", "#7f2f14"];

export function binner(values: number[], bins = SCALE.length) {
  const sorted = [...values].sort((a, b) => a - b);
  const thresholds = Array.from({ length: bins - 1 }, (_, i) => sorted[Math.floor(((i + 1) / bins) * sorted.length)]);
  return {
    thresholds,
    color(value: number | null | undefined) {
      if (value === null || value === undefined) return null;
      const index = thresholds.findIndex((t) => value < t);
      return SCALE[index === -1 ? bins - 1 : index];
    },
  };
}

/** Stable in-page anchor for an agency row: its ORI, or a slug of its name when unlinked. */
export function agencyAnchor(agency: Pick<Agency, "ori" | "name">): string {
  return agency.ori ?? `agency-${agency.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
}
