"""Assemble ``data/processed`` from cached downloads, legacy files and curated inputs."""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from iropo_pipeline import __version__, config
from iropo_pipeline.directory import DirectoryAgency, load_directory
from iropo_pipeline.fetch import Manifest, agencies_path, series_path, table_path
from iropo_pipeline.legacy import LEGACY_FILES, CrosswalkRow, crosswalk, read_legacy_workbook
from iropo_pipeline.matching import canonical, match_rows
from iropo_pipeline.offenders import DIMENSIONS, parse_offender_tables
from iropo_pipeline.series import Month, Year, annualize, latest_complete_year, parse_monthly
from iropo_pipeline.states import STATES, State
from iropo_pipeline.tables import AgencyTableRow, dedupe, parse_agency_tables

TABLE_TYPE_TO_DIRECTORY = {
    "city": "city",
    "metro_county": "county",
    "nonmetro_county": "county",
    "university": "university",
    "tribal": "tribal",
    "state_police": "state_police",
    "other": "other",
}
PUBLISHABLE_DISPOSITIONS = {"convicted", "pleaded_guilty", "no_contest"}
TOP_AGENCIES = 25


# --------------------------------------------------------------------------- helpers


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _is_scalar(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def _dumps(payload: Any, indent: int = 2, level: int = 0) -> str:
    """Pretty JSON that keeps scalar arrays and small flat objects on a single line."""
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if isinstance(payload, list) and all(_is_scalar(v) for v in payload):
        return compact
    if (
        isinstance(payload, dict)
        and len(compact) <= 240
        and all(
            _is_scalar(v)
            or (
                isinstance(v, (dict, list))
                and all(_is_scalar(x) for x in (v.values() if isinstance(v, dict) else v))
            )
            for v in payload.values()
        )
    ):
        return compact
    pad, inner = " " * (indent * level), " " * (indent * (level + 1))
    if isinstance(payload, dict):
        if not payload:
            return "{}"
        items = [
            f"{inner}{json.dumps(k)}: {_dumps(v, indent, level + 1)}" for k, v in payload.items()
        ]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if isinstance(payload, list):
        if not payload:
            return "[]"
        items = [inner + _dumps(v, indent, level + 1) for v in payload]
        return "[\n" + ",\n".join(items) + f"\n{pad}]"
    return json.dumps(payload, ensure_ascii=False)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dumps(payload) + "\n")


def _write_json_rows(path: Path, header: dict[str, Any], key: str, rows: list[dict]) -> None:
    """Pretty header, one compact JSON object per line: small and diff-friendly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    head = ",\n".join(f"  {json.dumps(k)}: {_dumps(v, level=1)}" for k, v in header.items())
    body = ",\n".join(
        "    " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows
    )
    path.write_text(f'{{\n{head},\n  "{key}": [\n{body}\n  ]\n}}\n')


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _compact(record: dict) -> dict:
    return {k: v for k, v in record.items() if v not in (None, {}, [], "")}


def _year_dict(year: Year) -> dict:
    return asdict(year)


def _monthly_block(months: list[Month], last_year: int) -> dict:
    kept = [m for m in months if config.SERIES_FIRST_YEAR <= int(m.month[:4]) <= last_year]
    return {
        "start": kept[0].month if kept else None,
        "offenses": [m.offenses for m in kept],
        "clearances": [m.clearances for m in kept],
    }


def _retrieved(manifest: Manifest, files: list[Path]) -> str | None:
    stamps = [e["retrieved_at"] for f in files if (e := manifest.get(f))]
    return max(stamps) if stamps else None


# --------------------------------------------------------------------------- agencies


def _agency_base(agency: DirectoryAgency) -> dict:
    return {
        "ori": agency.ori,
        "name": agency.name,
        "type": agency.type,
        "county": agency.counties,
        "lat": agency.latitude,
        "lon": agency.longitude,
        "nibrs": agency.nibrs,
        "nibrs_since": agency.nibrs_since,
    }


def build_state_agencies(
    state: State,
    directory: list[DirectoryAgency],
    rows: list[AgencyTableRow],
    matches: dict[AgencyTableRow, tuple[str, str]],
    legacy: list[CrosswalkRow],
) -> list[dict]:
    by_ori: dict[str, dict] = {a.ori: _agency_base(a) for a in directory}
    table_only: dict[tuple[str, str], dict] = {}
    for row in sorted(rows, key=lambda r: r.year):
        if row in matches:
            ori, method = matches[row]
            record = by_ori[ori]
            record["match"] = method
        else:
            directory_type = TABLE_TYPE_TO_DIRECTORY[row.agency_type]
            record = table_only.setdefault(
                (directory_type, canonical(row.name)),
                {"ori": None, "name": row.name, "type": directory_type, "match": "none"},
            )
        record["table_name"] = row.name
        record.setdefault("animal_cruelty", {})[str(row.year)] = row.animal_cruelty
        record.setdefault("total_offenses", {})[str(row.year)] = row.total_offenses
        if row.population:
            field = "enrollment" if row.agency_type == "university" else "population"
            if row.agency_type in ("city", "university"):
                record[field] = row.population

    for entry in legacy:
        if entry.current and entry.status in ("current", "likely_ocr_error"):
            record = by_ori.get(entry.current.ori)
            if record is not None:
                record["legacy_ori"] = entry.legacy.ori
                record["legacy_status"] = entry.status

    ordered = [
        "ori",
        "name",
        "type",
        "county",
        "lat",
        "lon",
        "nibrs",
        "nibrs_since",
        "table_name",
        "population",
        "enrollment",
        "animal_cruelty",
        "total_offenses",
        "match",
        "legacy_ori",
        "legacy_status",
    ]
    records = [
        _compact({k: rec.get(k) for k in ordered})
        for rec in list(by_ori.values()) + list(table_only.values())
    ]
    return sorted(records, key=lambda r: (r["name"].lower(), r.get("ori") or ""))


# --------------------------------------------------------------------------- registry gate


def publishable(record: dict, today: dt.date | None = None) -> bool:
    """Only verified, adjudicated, officially sourced, unexpired records may ever be published.

    Mirrors the policy on https://iropo.org/registry/: two independent reviewers, at least one
    court record or official registry source, no removed or disputed records, and listings expire
    with the source jurisdiction's retention period.
    """
    today = today or dt.date.today()
    if record.get("status") != "verified":
        return False
    if (record.get("case") or {}).get("disposition") not in PUBLISHABLE_DISPOSITIONS:
        return False
    reviewers = {r.strip().lower() for r in (record.get("verification") or {}).get("reviewers", [])}
    if len(reviewers) < 2:
        return False
    listing = record.get("listing") or {}
    if listing.get("removed_at"):
        return False
    expires = listing.get("expires_at")
    if expires and dt.date.fromisoformat(expires) <= today:
        return False
    sources = record.get("sources") or []
    return any(s.get("type") in {"court_record", "official_registry"} for s in sources)


# --------------------------------------------------------------------------- main build


def build_all(log=print) -> None:
    manifest = Manifest.load()
    national_payload_path = series_path("US")
    if not national_payload_path.exists():
        raise SystemExit("No cached data found. Run `iropo-data fetch` first.")
    out = config.PROCESSED_DIR

    log("Loading agency directory")
    directory = {
        s.abbr: load_directory(agencies_path(s), s.abbr)
        for s in STATES
        if agencies_path(s).exists()
    }
    all_directory = [a for agencies in directory.values() for a in agencies]

    log("Parsing CDE monthly series")
    national_payload = _load_json(national_payload_path)
    published_tables = [
        y
        for y in range(config.TABLE_FIRST_YEAR, latest_complete_year(national_payload) + 1)
        if table_path(y, "agencies").exists()
    ]
    # The newest year with final annual tables is the latest year the FBI considers complete.
    last_year = (
        max(published_tables) if published_tables else latest_complete_year(national_payload)
    )
    national_months = parse_monthly(national_payload, national=True)
    national_years = annualize(national_months, config.SERIES_FIRST_YEAR, last_year)
    state_months = {
        s.abbr: parse_monthly(_load_json(series_path(s.abbr)), national=False)
        for s in STATES
        if series_path(s.abbr).exists()
    }

    log("Parsing NIBRS agency tables")
    table_years = published_tables
    rows: list[AgencyTableRow] = []
    for year in table_years:
        rows.extend(parse_agency_tables(table_path(year, "agencies"), year, log))
    rows = dedupe(rows)
    matches = match_rows(rows, all_directory)
    rows_by_state: dict[str, list[AgencyTableRow]] = defaultdict(list)
    for row in rows:
        rows_by_state[row.state].append(row)
    log(f"  {len(rows):,} agency-year rows, {len(matches) / max(len(rows), 1):.1%} linked to ORIs")

    log("Parsing offender demographics")
    offender_years = [y for y in table_years if table_path(y, "offenders").exists()]
    offenders = {y: parse_offender_tables(table_path(y, "offenders")) for y in offender_years}

    log("Cross-checking legacy spreadsheets")
    legacy_dir = config.LEGACY_DIR / "agency-directories"
    legacy = {
        st: crosswalk(read_legacy_workbook(legacy_dir / name, st), directory.get(st, []))
        for st, name in LEGACY_FILES.items()
    }

    log("Writing per-state agency files")
    agencies_by_state: dict[str, list[dict]] = {}
    for state in STATES:
        records = build_state_agencies(
            state,
            directory.get(state.abbr, []),
            rows_by_state.get(state.abbr, []),
            matches,
            legacy.get(state.abbr, []),
        )
        agencies_by_state[state.abbr] = records
        _write_json_rows(
            out / "agencies" / f"{state.abbr}.json",
            {"state": state.abbr, "name": state.name, "table_years": table_years},
            "agencies",
            records,
        )

    log("Writing state and national summaries")
    states_payload = []
    for state in STATES:
        months = state_months.get(state.abbr, [])
        state_rows = rows_by_state.get(state.abbr, [])
        per_year = defaultdict(list)
        for row in state_rows:
            per_year[row.year].append(row)
        crosswalk_rows = legacy.get(state.abbr)
        states_payload.append(
            {
                "abbr": state.abbr,
                "name": state.name,
                "slug": state.slug,
                "fips": state.fips,
                "annual": [
                    _year_dict(y) for y in annualize(months, config.SERIES_FIRST_YEAR, last_year)
                ],
                "monthly": _monthly_block(months, last_year),
                "agencies": {
                    "directory": len(directory.get(state.abbr, [])),
                    "directory_nibrs": sum(a.nibrs for a in directory.get(state.abbr, [])),
                    "reporting": {str(y): len(per_year.get(y, [])) for y in table_years},
                    "with_cases": {
                        str(y): sum(1 for r in per_year.get(y, []) if (r.animal_cruelty or 0) > 0)
                        for y in table_years
                    },
                    "table_offenses": {
                        str(y): sum(r.animal_cruelty or 0 for r in per_year.get(y, []))
                        for y in table_years
                    },
                },
                "legacy": (
                    {
                        "rows": len(crosswalk_rows),
                        **dict(Counter(r.status for r in crosswalk_rows)),
                        "needs_review": sum(
                            1
                            for r in crosswalk_rows
                            if r.status == "current" and not r.name_consistent
                        ),
                    }
                    if crosswalk_rows
                    else None
                ),
            }
        )
    _write_json(
        out / "states.json",
        {
            "last_full_year": last_year,
            "series_first_year": config.SERIES_FIRST_YEAR,
            "table_years": table_years,
            "states": states_payload,
        },
    )

    latest_rows = [r for r in rows if r.year == table_years[-1]]
    top = sorted(
        (r for r in latest_rows if r.animal_cruelty), key=lambda r: -(r.animal_cruelty or 0)
    )
    by_year_rows: dict[int, list[AgencyTableRow]] = defaultdict(list)
    for row in rows:
        by_year_rows[row.year].append(row)
    directory_by_ori = {a.ori: a for a in all_directory}

    def top_entry(row: AgencyTableRow) -> dict:
        ori = matches.get(row, (None, ""))[0]
        return _compact(
            {
                "ori": ori,
                "name": directory_by_ori[ori].name if ori else row.name,
                "table_name": row.name,
                "state": row.state,
                "type": TABLE_TYPE_TO_DIRECTORY[row.agency_type],
                "offenses": row.animal_cruelty,
                "population": row.population if row.agency_type == "city" else None,
            }
        )

    _write_json(
        out / "national.json",
        {
            "last_full_year": last_year,
            "series_first_year": config.SERIES_FIRST_YEAR,
            "table_years": table_years,
            "annual": [_year_dict(y) for y in national_years],
            "monthly": _monthly_block(national_months, last_year),
            "tables": {
                str(y): {
                    "agencies": len(by_year_rows[y]),
                    "with_cases": sum(1 for r in by_year_rows[y] if (r.animal_cruelty or 0) > 0),
                    "offenses": sum(r.animal_cruelty or 0 for r in by_year_rows[y]),
                    "states": len({r.state for r in by_year_rows[y]}),
                }
                for y in table_years
            },
            "top_agencies": [top_entry(r) for r in top[:TOP_AGENCIES]],
            "offenders": {
                "years": offender_years,
                "dimensions": list(DIMENSIONS),
                "by_year": {str(y): offenders[y] for y in offender_years},
            },
        },
    )

    log("Writing legacy crosswalks")
    legacy_fields = [
        "state",
        "sheet",
        "legacy_agency",
        "legacy_city",
        "legacy_county",
        "legacy_ori",
        "status",
        "needs_review",
        "current_ori",
        "current_name",
        "current_type",
        "current_county",
    ]
    all_legacy_rows = []
    for st, crosswalk_rows in legacy.items():
        flat = [
            {
                "state": st,
                "sheet": r.legacy.sheet,
                "legacy_agency": r.legacy.agency,
                "legacy_city": r.legacy.city,
                "legacy_county": r.legacy.county,
                "legacy_ori": r.legacy.ori,
                "status": r.status,
                "needs_review": "yes" if r.status == "current" and not r.name_consistent else "",
                "current_ori": r.current.ori if r.current else "",
                "current_name": r.current.name if r.current else "",
                "current_type": r.current.type if r.current else "",
                "current_county": (r.current.counties or "") if r.current else "",
            }
            for r in crosswalk_rows
        ]
        all_legacy_rows.extend(flat)
        _write_csv(out / "legacy" / f"{st}-crosswalk.csv", legacy_fields, flat)

    log("Writing open-data CSV exports")
    open_dir = out / "open-data"
    _write_csv(
        open_dir / "agencies.csv",
        [
            "ori",
            "name",
            "type",
            "state",
            "counties",
            "latitude",
            "longitude",
            "nibrs",
            "nibrs_since",
        ],
        [{**asdict(a), "nibrs": "yes" if a.nibrs else "no"} for a in all_directory],
    )
    _write_csv(
        open_dir / "animal-cruelty-by-agency.csv",
        [
            "year",
            "state",
            "ori",
            "agency_name",
            "agency_type",
            "population",
            "total_offenses",
            "animal_cruelty",
            "ori_match",
        ],
        [
            {
                "year": r.year,
                "state": r.state,
                "ori": matches.get(r, ("", ""))[0],
                "agency_name": r.name,
                "agency_type": r.agency_type,
                "population": r.population if r.agency_type == "city" else "",
                "total_offenses": r.total_offenses,
                "animal_cruelty": r.animal_cruelty,
                "ori_match": matches.get(r, ("", "none"))[1],
            }
            for r in sorted(rows, key=lambda r: (r.year, r.state, r.name))
        ],
    )
    series_fields = [
        "year",
        "state",
        "offenses",
        "clearances",
        "clearance_rate",
        "rate_per_100k",
        "coverage_pct",
        "population",
        "covered_population",
        "months_reported",
    ]
    series_rows = [{"state": "US", **_year_dict(y)} for y in national_years]
    for entry in states_payload:
        series_rows.extend({"state": entry["abbr"], **y} for y in entry["annual"])
    _write_csv(open_dir / "animal-cruelty-by-state.csv", series_fields, series_rows)
    demo_rows = []
    for year in offender_years:
        for dimension, table in offenders[year].items():
            for group, count in table["animal_cruelty"].items():
                demo_rows.append(
                    {
                        "year": year,
                        "dimension": dimension,
                        "group": group,
                        "animal_cruelty": count,
                        "all_offenses": table["all_offenses"].get(group),
                    }
                )
    _write_csv(
        open_dir / "animal-cruelty-offenders.csv",
        ["year", "dimension", "group", "animal_cruelty", "all_offenses"],
        demo_rows,
    )
    _write_csv(open_dir / "legacy-ori-crosswalk.csv", legacy_fields, all_legacy_rows)

    log("Publishing curated registries and verified records")
    registries = _load_json(config.CURATED_DIR / "official-registries.json")
    _write_json(out / "official-registries.json", registries)
    records_path = Path(
        os.environ.get("IROPO_RECORDS_PATH", config.CURATED_DIR / "registry-records.json")
    )
    records = _load_json(records_path) if records_path.exists() else []
    published = [r for r in records if publishable(r)]
    _write_json(out / "registry.json", {"published": len(published), "records": published})

    log("Writing provenance")
    retrieved = _retrieved(manifest, [national_payload_path])
    sources = _sources(manifest, table_years, offender_years, registries)
    _write_json(out / "sources.json", sources)
    _write_json(
        out / "meta.json",
        {
            "pipeline_version": __version__,
            "data_retrieved_at": max(
                filter(None, [s.get("retrieved_at") for s in sources]), default=retrieved
            ),
            "cde_last_refresh": (national_payload.get("cde_properties") or {})
            .get("last_refresh_date", {})
            .get("UCR"),
            "cde_max_data_date": (national_payload.get("cde_properties") or {})
            .get("max_data_date", {})
            .get("UCR"),
            "last_full_year": last_year,
            "table_years": table_years,
            "counts": {
                "states": len(states_payload),
                "directory_agencies": len(all_directory),
                "agency_year_rows": len(rows),
                "linked_rows": len(matches),
                "published_registry_records": len(published),
                "official_registries": len(registries.get("registries", [])),
            },
        },
    )
    log(f"Done. Outputs in {out.relative_to(config.REPO_ROOT)}")


def _sources(
    manifest: Manifest, table_years: list[int], offender_years: list[int], registries: dict
) -> list[dict]:
    def files(prefix: str) -> list[dict]:
        return [
            {"path": path, **entry}
            for path, entry in sorted(manifest.entries.items())
            if path.startswith(prefix)
        ]

    def stamp(entries: list[dict]) -> str | None:
        return max((e["retrieved_at"] for e in entries), default=None)

    directory_files = files("cde/agencies/")
    series_files = files(f"cde/nibrs-{config.ANIMAL_CRUELTY_CODE}/")
    agency_tables = [f for f in files("fbi/nibrs-tables/") if f["path"].endswith("-agencies.zip")]
    offender_tables = [
        f for f in files("fbi/nibrs-tables/") if f["path"].endswith("-offenders.zip")
    ]
    public_domain = "Public domain (U.S. federal government work)"
    return [
        {
            "id": "fbi-cde-agency-directory",
            "title": "FBI Crime Data Explorer: law enforcement agency directory",
            "publisher": "Federal Bureau of Investigation, Uniform Crime Reporting Program",
            "url": "https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi",
            "endpoint": "/agency/byStateAbbr/{state}",
            "used_for": "ORIs, agency names and types, counties, coordinates and NIBRS status",
            "coverage": f"{len(directory_files)} jurisdictions (50 states and DC)",
            "license": public_domain,
            "retrieved_at": stamp(directory_files),
            "files": len(directory_files),
        },
        {
            "id": "fbi-cde-nibrs-animal-cruelty-series",
            "title": "FBI Crime Data Explorer: NIBRS animal cruelty (offense 720) monthly series",
            "publisher": "Federal Bureau of Investigation, Uniform Crime Reporting Program",
            "url": "https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/explorer/crime/crime-trend",
            "endpoint": "/nibrs/{national|state/{state}}/720?type=counts",
            "used_for": "Offenses, clearances, population coverage and rates by month and year",
            "coverage": f"{config.SERIES_FIRST_YEAR} onward, national and {len(series_files) - 1} "
            "jurisdictions",
            "license": public_domain,
            "retrieved_at": stamp(series_files),
            "files": len(series_files),
        },
        {
            "id": "fbi-nibrs-offense-type-by-agency",
            "title": "FBI NIBRS Tables: Offense Type by Agency",
            "publisher": "Federal Bureau of Investigation, Uniform Crime Reporting Program",
            "url": "https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads",
            "used_for": "Animal cruelty and total offenses reported by each agency, per year",
            "coverage": f"{table_years[0]}-{table_years[-1]}" if table_years else "",
            "license": public_domain,
            "retrieved_at": stamp(agency_tables),
            "checksums": {Path(f["path"]).name: f["sha256"] for f in agency_tables},
        },
        {
            "id": "fbi-nibrs-offenders",
            "title": "FBI NIBRS Tables: Offenders by age, sex, race and age category",
            "publisher": "Federal Bureau of Investigation, Uniform Crime Reporting Program",
            "url": "https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads",
            "used_for": "Demographics of known animal cruelty offenders compared with all offenses",
            "coverage": f"{offender_years[0]}-{offender_years[-1]}" if offender_years else "",
            "license": public_domain,
            "retrieved_at": stamp(offender_tables),
            "checksums": {Path(f["path"]).name: f["sha256"] for f in offender_tables},
        },
        {
            "id": "official-animal-abuser-registries",
            "title": "Official government animal abuser registries (curated catalog)",
            "publisher": "IROPO contributors",
            "url": "https://github.com/the-robots/iropo.org/blob/main/data/curated/official-registries.json",
            "used_for": "Links to registries run by state and local governments",
            "coverage": f"{len(registries.get('registries', []))} registries",
            "license": "CC0-1.0",
            "retrieved_at": registries.get("verified_on"),
        },
        {
            "id": "legacy-nlets-directory-1977",
            "title": "NLETS directory of criminal justice agency ORIs (LEAA grant 75-SS-99-6018)",
            "publisher": "Law Enforcement Assistance Administration / NCJRS (document 75873)",
            "url": "https://github.com/the-robots/iropo.org/tree/main/docs/reference",
            "used_for": "Historical ORIs for NC, ND and NY (legacy spreadsheets), cross-checked "
            "against the current FBI directory",
            "coverage": "North Carolina, North Dakota (partial), New York",
            "license": public_domain,
            "retrieved_at": None,
        },
    ]
