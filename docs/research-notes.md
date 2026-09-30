# Research notes

Working notes about IROPO's data sources. Keep them factual and cite sources.

## FBI Crime Data Explorer (CDE)

- Documentation: <https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi>
- Animal cruelty is NIBRS offense code **720**, a Group A offense since January 2016. It covers
  simple/gross neglect, intentional abuse and torture, organized abuse (dog and cock fighting) and
  animal sexual abuse.
- The legacy "SAPI" endpoints used by IROPO's first scripts
  (`https://api.usa.gov/crime/fbi/sapi/api/...`) have been retired and return 404. That is why the
  original `api-test.py` returned empty results.
- Current endpoints (same paths on both hosts):
  - documented gateway: `https://api.usa.gov/crime/fbi/cde/...` with `API_KEY=<api.data.gov key>`
    (`DEMO_KEY` is limited to about 10 requests per hour);
  - public backend of the CDE website: `https://cde.ucr.cjis.gov/LATEST/...` (no key).
- Useful endpoints:
  - `/agency/byStateAbbr/{ST}` — every agency in a state, keyed by county (agencies serving several
    counties appear more than once).
  - `/nibrs/national/720?type=counts&from=01-2016&to=12-2025` and `/nibrs/state/{ST}/720?...` —
    monthly offenses and clearances, rates per 100,000, population coverage and populations.
    `cde_properties.max_data_date` gives the latest month published.
  - `/nibrs/agency/{ORI}/720?...` — the same for one agency (not used; one request per agency).
  - `/s3/signedurl?key=nibrs/tables/{year}/{name}.zip` — signed download links for the NIBRS
    publication tables. `name` is `stateTables` (2020–2023, one workbook per state),
    `statesAndFederal` (2024 onward, one national workbook) or `offenders`.
- 2020 and part of 2021 tables are legacy `.xls` files; later years are `.xlsx`. Some tables nest
  sub-agencies under group headers (e.g. `State Park Rangers:`) using cell indentation.

## ORI numbers

ORI Number – nine characters: the unique NCIC Originating Agency Identifier assigned to each
agency. It must be included in each Group "A" Incident Report or Group "B" Arrest Report. Federal
agencies' ORIs combine the ORI of the agency with jurisdiction where the incident occurred and the
Federal Agency Identifier (FID) assigned by the FBI's UCR Program.

Example: the ORI for the New York City Police Department is `NY0303000`. If the FBI in New York
City reports a crime, the ORI would be `NY03030JF`: `NY03030` for New York City as the location and
`JF` for the FBI as the reporting agency.

Aberdeen, NC police department: `NC0630100` (still current in the FBI directory).

## Legacy agency spreadsheets

`data/raw/legacy/agency-directories/localAndStateAgencies-*.xlsx` were transcribed by OCR from the
1977 NLETS directory (`docs/reference/75873NCJRS.pdf`). Typical OCR errors: `I`/`L` for `1`,
`O`/`D`/`Q` for `0`, `S` for `5`, `B` for `8`, and `0RI` for `ORI` in headers. The ND workbook also
contains copies of the New York sheets and its North Dakota sheet stops at "K". The pipeline
cross-checks every legacy ORI against the current FBI directory and publishes the result in
`data/processed/legacy/`.

## Secrets

API keys and account identifiers must never be committed to the repository. If a key was ever
committed to a public branch, treat it as compromised and revoke or regenerate it with the issuing
service.
