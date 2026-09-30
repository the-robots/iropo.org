export type YearCounts = Record<string, number | null>;

export interface AnnualPoint {
  year: number;
  months_reported: number;
  offenses: number | null;
  clearances: number | null;
  coverage_pct: number;
  population: number | null;
  covered_population: number | null;
  rate_per_100k: number | null;
  clearance_rate: number | null;
}

export interface MonthlySeries {
  start: string | null;
  offenses: (number | null)[];
  clearances: (number | null)[];
}

export interface StateSummary {
  abbr: string;
  name: string;
  slug: string;
  fips: string;
  annual: AnnualPoint[];
  monthly: MonthlySeries;
  agencies: {
    directory: number;
    directory_nibrs: number;
    reporting: Record<string, number>;
    with_cases: Record<string, number>;
    table_offenses: Record<string, number>;
  };
  legacy: null | {
    rows: number;
    current?: number;
    likely_ocr_error?: number;
    federal?: number;
    not_found?: number;
    needs_review: number;
  };
}

export interface StatesFile {
  last_full_year: number;
  series_first_year: number;
  table_years: number[];
  states: StateSummary[];
}

export type DemographicTable = Record<string, number>;

export interface OffenderDimension {
  animal_cruelty: DemographicTable;
  all_offenses: DemographicTable;
}

export interface NationalFile {
  last_full_year: number;
  series_first_year: number;
  table_years: number[];
  annual: AnnualPoint[];
  monthly: MonthlySeries;
  tables: Record<string, { agencies: number; with_cases: number; offenses: number; states: number }>;
  top_agencies: {
    ori?: string;
    name: string;
    table_name: string;
    state: string;
    type: AgencyType;
    offenses: number;
    population?: number;
  }[];
  offenders: {
    years: number[];
    dimensions: string[];
    by_year: Record<string, Record<"age_category" | "age" | "sex" | "race", OffenderDimension>>;
  };
}

export type AgencyType =
  | "city"
  | "county"
  | "university"
  | "other"
  | "other_state"
  | "state_police"
  | "tribal"
  | "federal";

export interface Agency {
  ori?: string;
  name: string;
  type: AgencyType;
  county?: string;
  lat?: number;
  lon?: number;
  nibrs?: boolean;
  nibrs_since?: string;
  table_name?: string;
  population?: number;
  enrollment?: number;
  animal_cruelty?: YearCounts;
  total_offenses?: YearCounts;
  match?: "exact" | "normalized" | "tokens" | "none";
  legacy_ori?: string;
  legacy_status?: "current" | "likely_ocr_error";
}

export interface AgencyFile {
  state: string;
  name: string;
  table_years: number[];
  agencies: Agency[];
}

export interface Source {
  id: string;
  title: string;
  publisher: string;
  url: string;
  endpoint?: string;
  used_for: string;
  coverage: string;
  license: string;
  retrieved_at: string | null;
  files?: number;
  checksums?: Record<string, string>;
}

export interface Meta {
  pipeline_version: string;
  data_retrieved_at: string;
  cde_last_refresh: string | null;
  cde_max_data_date: string | null;
  last_full_year: number;
  table_years: number[];
  counts: Record<string, number>;
}

export interface OfficialRegistry {
  id: string;
  jurisdiction: string;
  level: "state" | "county" | "city";
  state: string;
  name: string;
  operator: string;
  url: string;
  access: "public" | "restricted" | "unknown";
  established?: string | null;
  legal_citation?: string | null;
  retention?: string | null;
  status: "active" | "defunct" | "unknown";
  verified_on?: string;
  notes?: string | null;
  sources: string[];
}

export interface RegistryProposal {
  id: string;
  jurisdiction: string;
  level: "state" | "county" | "city";
  state: string;
  bill: string;
  detail: string;
  sources: string[];
}

export interface RegistriesFile {
  verified_on: string;
  notes?: string;
  registries: OfficialRegistry[];
  proposals?: RegistryProposal[];
  leads?: { id: string; jurisdiction: string; state: string; finding: string; reason: string; sources: string[] }[];
}

export interface RegistryFile {
  published: number;
  records: unknown[];
}
