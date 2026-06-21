# IROPO — International Registry of Pet Offenders

IROPO is a planning-stage animal-welfare advocacy project focused on documenting and tracking people who have harmed animals using public and official data sources.

> 🚧 **Planning phase:** the project is still being scoped. The immediate focus is building a data-mining and scraping pipeline to gather offender data for each city and state across the United States before considering any broader expansion.

## What is IROPO?

IROPO stands for the **International Registry of Pet Offenders**. The long-term concept is a registry that lists people who have caused harm or affliction to animals, with the goal of supporting animal-welfare advocacy and making fragmented public information easier to find and review.

At this stage, the repository is primarily a research and planning workspace. It contains early notes, prototype scripts, reference material, and sample source files that may help shape the future data pipeline and site architecture.

## Project status

This repository is not yet a finished website or production data service. It is currently being used to:

- collect and evaluate candidate data sources
- understand how available FBI and agency datasets are structured
- test early import ideas using ORI-based lookups
- outline the work needed to build a reliable, reviewable source of truth

The immediate near-term priority is proposed data aggregation work across the US, starting city-by-city and state-by-state with states already represented in this repository.

## Mission and goals

The existing project objectives remain the foundation for the work here:

- **Allocate funds and resources to help build the site.** Identify the time, tools, hosting, legal review, and volunteer capacity needed to move from research into an operational project.
- **Gather varying data sources into one primary source of truth.** Evaluate public and official records, normalize them into a consistent format, and document where each record came from.
- **Decide on a framework to surface data on iropo.org.** Assess whether the project should remain static, use GitHub Pages for limited publishing, or eventually move to an application-backed site and database.
- **Build out the interface.** Design a usable public experience for browsing, searching, and understanding the data once sourcing and verification are mature enough.
- **Promote across social media.** Build awareness, attract volunteers and subject-matter expertise, and create feedback loops with animal-welfare communities.

## Data sources

Known data sources and references already present in this repository include:

- **FBI Crime Data Explorer / NIBRS documentation**  
  <https://crime-data-explorer.fr.cloud.gov/pages/docApi>
- **FBI Crime Data API via api.usa.gov** for animal-cruelty offender counts and related lookups
- **NCIC ORI numbers** used to identify reporting agencies
- **Per-state agency spreadsheets** such as `localAndStateAgencies-NC.xlsx`, `localAndStateAgencies-ND.xlsx`, and `localAndStateAgencies-NY.xlsx`
- **FBI offender demographic spreadsheets** in `Offenders/`
- **Reference manuals and PDFs** that may help interpret identifiers, agency data, and public-record workflows

### What is an ORI?

An **ORI** is a nine-character **Originating Agency Identifier** used in NCIC and related criminal-justice reporting systems to identify a reporting agency. The working notes in this repository include examples such as `NY0303000` for the New York City Police Department and `NC0630100` for Aberdeen, North Carolina.

## Repository structure

| Path | Purpose |
| --- | --- |
| `README.md` | Project overview, planning status, and roadmap |
| `CONTRIBUTING.md` | Basic contributor guidance for this planning-stage repository |
| `iropo.org.md` | Scratch notes about sources, ORIs, and API research |
| `api-test.py` | Prototype script that reads an agency spreadsheet and queries the FBI API by ORI |
| `api-test-columns.py` | Prototype script for inspecting spreadsheet columns |
| `localAndStateAgencies-*.xlsx` | Agency and ORI lists for states currently being explored |
| `Offenders/` | FBI demographic spreadsheets related to offender data |
| `*.pdf`, `*.rtf` | Reference material and manuals used during research |
| `.github/workflows/` | Simple workflow-dispatch jobs for the prototype Python scripts |

## Getting started with the data scripts

The Python files in this repository are exploratory prototypes, not production scrapers. They are useful for learning the source data and validating that ORI-based requests work as expected.

1. Use Python 3.11+ (or another modern Python 3 release).
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the current script dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and add a valid API key locally:

   ```bash
   cp .env.example .env
   ```

   Then set `FBI_API_KEY` in `.env` or your shell environment.

5. Run one of the exploratory scripts:

   ```bash
   python api-test-columns.py
   python api-test.py
   ```

`api-test.py` expects `FBI_API_KEY` to be available in the environment. If these scripts are run in GitHub Actions, store the key as a repository or organization secret rather than committing it to the repository.

## Security and secrets

- Never commit API keys, access tokens, account IDs, or personal account email addresses.
- Use a local `.env` file for development and GitHub Actions secrets for automation.
- If a key is ever committed to a public repository, treat it as compromised and revoke or rotate it with the issuing service.

## Roadmap / TODO

The following checklist is a proposed roadmap based on the current objectives and the repository's present state.

### Phase 0 — Foundations & housekeeping

- [ ] Revoke and rotate the previously exposed data.gov / FBI API key.
- [ ] Move secrets to environment variables and GitHub Actions secrets; keep `.env.example` and `.gitignore` up to date.
- [ ] Add and maintain a `requirements.txt` for the exploratory Python scripts.
- [ ] Add `CONTRIBUTING.md` and make sure `CODE_OF_CONDUCT.md` remains linked from project documentation.
- [ ] Clean up stray and temporary files such as spreadsheet lock files before future releases.

### Phase 1 — Funding & resources

- [ ] Identify the funds, hosting, tooling, and operational resources needed to build and maintain the project.
- [ ] Identify volunteers, contributors, and partner organizations who can help with research, legal review, engineering, design, and moderation.
- [ ] Clarify which responsibilities require subject-matter expertise before any public launch.

### Phase 2 — Data aggregation (immediate focus)

- [ ] Define the canonical schema for an offender or case record, including fields, identifiers, source references, and dates.
- [ ] Catalog and evaluate candidate data sources, including FBI NIBRS animal-cruelty data, state and local agency records, and other public court or records systems.
- [ ] Build a US city/state coverage matrix to track where data sources exist and how complete they are.
- [ ] Build prototype scrapers and importers for city-by-city and state-by-state collection, starting with the states already represented here: NC, ND, and NY.
- [ ] Establish a verification workflow and a single source-of-truth datastore for reviewed records.
- [ ] Define processes for accuracy review, corrections, removals, and dispute handling.
- [ ] Record data provenance for every imported record so contributors can trace where information came from.

### Phase 3 — Framework & architecture

- [ ] Decide on the framework and deployment model for presenting data on `iropo.org`.
- [ ] Evaluate whether GitHub Pages should remain part of the publishing strategy or whether a database-backed application is needed.
- [ ] Design the data storage model, ingestion pipeline, and update cadence.
- [ ] Define whether the project needs a public API or another structured access layer.

### Phase 4 — Build the interface

- [ ] Build the public-facing interface for browsing and searching the registry.
- [ ] Implement search and filtering by location, name, offense type, and source metadata.
- [ ] Add accessibility, responsive design, and basic SEO considerations from the start.
- [ ] Provide clear source citations, status indicators, and correction/reporting affordances in the UI.

### Phase 5 — Launch & outreach

- [ ] Set up analytics, contact paths, and contributor/user feedback mechanisms.
- [ ] Promote the project across social media and relevant animal-welfare communities.
- [ ] Establish an ongoing maintenance plan for updates, reviews, corrections, and archival decisions.
- [ ] Publish clear expectations for what has and has not yet been verified when data begins to appear publicly.

## How to contribute

Contributions are welcome, especially during the planning phase. Helpful contributions may include:

- identifying or documenting public/official data sources
- improving the prototype scripts and data-import approach
- proposing schema, verification, or correction workflows
- helping plan the site architecture and public interface
- reviewing documentation for clarity and scope

Please start with [`CONTRIBUTING.md`](CONTRIBUTING.md) and follow the community expectations in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). If you want to help shape the project process further, proposing a fuller `CONTRIBUTING.md`, data policy, or governance document would also be useful.

## Legal & ethical considerations

Because this project concerns information about identifiable people and alleged or adjudicated harm to animals, contributors should work carefully and conservatively:

- data should come from public, official, or otherwise reviewable records
- accuracy, verification, and provenance matter more than speed
- any eventual public listing should have a correction or removal path
- contributors should be mindful of privacy, defamation, and jurisdiction-specific legal risks when handling or publishing information

These points are not legal advice; they are planning considerations that should be addressed before any public registry is treated as authoritative.

## License

This project is licensed under [CC0-1.0](LICENSE).

## Contact / community

If you want to help, use GitHub issues or pull requests for now. Additional contact or community channels can be added here later if the project adopts a mailing list, GitHub Discussions, or another volunteer coordination space.
