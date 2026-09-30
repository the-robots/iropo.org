# IROPO data pipeline

The pipeline turns official, public FBI data into the normalized datasets in
[`data/processed/`](../data/processed) that power [iropo.org](https://iropo.org). It is the
"collect → normalize → verify → publish" part of the project's data flow.

## What it builds

| Output | Contents |
| --- | --- |
| `data/processed/national.json` | U.S. animal-cruelty offenses, clearances, rates and NIBRS coverage by year, plus offender demographics (age, sex, race, adult/juvenile) |
| `data/processed/states.json` | The same yearly and monthly series for every state and DC, plus agency and coverage counts |
| `data/processed/agencies/<ST>.json` | Every law-enforcement agency in the FBI directory (ORI, type, county, NIBRS status, coordinates) joined to its yearly animal-cruelty offense counts |
| `data/processed/legacy/<ST>-crosswalk.csv` | Legacy 1977 NLETS directory ORIs (NC, ND, NY spreadsheets) checked against today's FBI directory |
| `data/processed/open-data/*.csv` | Flat CSV exports published on the website |
| `data/processed/sources.json` | Provenance for every dataset: URLs, retrieval times and checksums |

Hand-maintained inputs live in [`data/curated/`](../data/curated) and JSON Schemas in
[`data/schema/`](../data/schema).

## Sources

* **FBI Crime Data Explorer (CDE) API** – agency directory (`/agency/byStateAbbr/{state}`) and
  monthly NIBRS offense counts for offense code `720` (Animal Cruelty) nationally and by state.
* **CDE "NIBRS Tables" downloads** – *Offense Type by Agency* (2020 onward) and *Offenders*
  demographic tables.
* **Legacy spreadsheets** in `data/raw/legacy/` – kept for provenance and cross-checking only.

## Running it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
cd pipeline
uv sync                      # install dependencies into .venv
uv run iropo-data fetch      # download raw data into data/cache (≈130 polite requests)
uv run iropo-data build      # rebuild data/processed
uv run iropo-data validate   # check outputs against the JSON Schemas
uv run pytest                # unit tests
uv run ruff check .          # lint
```

`uv run iropo-data all` runs fetch, build and validate in one go. Pass `--refresh` to re-download
files that are already cached, or `--states NC,NY` to limit the directory/series fetch.

### API keys

No key is required: without one the pipeline uses the public backend of the CDE website
(`https://cde.ucr.cjis.gov/LATEST`) and throttles itself. If you have a free
[api.data.gov key](https://api.data.gov/signup/), put it in `FBI_API_KEY` (see
[`.env.example`](../.env.example)) and the documented gateway
(`https://api.usa.gov/crime/fbi/cde`) is used for API calls instead. Never commit keys.

## Notes on the data

* Animal cruelty became a NIBRS Group A offense in 2016. Year-over-year growth partly reflects more
  agencies reporting through NIBRS, so compare **rates** and check **population coverage**.
* CDE monthly series and the annual publication tables are produced separately and can differ
  slightly (late submissions, 12-month reporting rules).
* The FBI tables name agencies but do not include ORIs. The pipeline links table rows to the FBI
  agency directory by state, agency type and normalized name, and records how each match was made
  (`match` field). Unmatched rows are kept without an ORI.
* No individual-level records are produced. The canonical individual record format is defined in
  [`data/schema/registry-record.schema.json`](../data/schema/registry-record.schema.json) for use
  once legal review and the verification workflow are in place.
