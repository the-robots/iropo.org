import fs from "node:fs";
import path from "node:path";
import type {
  AgencyFile,
  Meta,
  NationalFile,
  RegistriesFile,
  RegistryFile,
  Source,
  StatesFile,
  StateSummary,
} from "./types";

/** Build-time access to the pipeline's source-of-truth datasets in data/processed. */
export const DATA_DIR = path.resolve(process.cwd(), "data/processed");

function read<T>(relative: string): T {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, relative), "utf8")) as T;
}

export const national = read<NationalFile>("national.json");
export const statesFile = read<StatesFile>("states.json");
export const states: StateSummary[] = statesFile.states;
export const meta = read<Meta>("meta.json");
export const sources = read<Source[]>("sources.json");
export const officialRegistries = read<RegistriesFile>("official-registries.json");
export const registry = read<RegistryFile>("registry.json");

export const LATEST_YEAR = statesFile.last_full_year;
export const TABLE_YEARS = statesFile.table_years;
export const LATEST_TABLE_YEAR = TABLE_YEARS[TABLE_YEARS.length - 1];

const agencyCache = new Map<string, AgencyFile>();

export function agenciesFor(abbr: string): AgencyFile {
  if (!agencyCache.has(abbr)) {
    agencyCache.set(abbr, read<AgencyFile>(`agencies/${abbr}.json`));
  }
  return agencyCache.get(abbr)!;
}

export function stateBySlug(slug: string): StateSummary | undefined {
  return states.find((s) => s.slug === slug);
}

export function stateByAbbr(abbr: string): StateSummary | undefined {
  return states.find((s) => s.abbr === abbr);
}

/** Files in data/processed/open-data (served at /data/<file>). */
export function openDataFiles(): { name: string; bytes: number; rows: number }[] {
  const dir = path.join(DATA_DIR, "open-data");
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".csv"))
    .sort()
    .map((name) => {
      const full = path.join(dir, name);
      const text = fs.readFileSync(full, "utf8");
      return { name, bytes: fs.statSync(full).size, rows: Math.max(text.trimEnd().split("\n").length - 1, 0) };
    });
}

export function readOpenData(name: string): string {
  return fs.readFileSync(path.join(DATA_DIR, "open-data", name), "utf8");
}
