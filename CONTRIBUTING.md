# Contributing to IROPO

Thank you for considering a contribution. IROPO is a volunteer-driven, open-data project, and every
improvement to its sources, code or documentation helps.

## Before you start

- Read the project overview in [`README.md`](README.md) and the [registry policy](https://iropo.org/registry/).
- Follow the community expectations in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- Do not commit API keys, tokens, account identifiers or personal contact details.
- Never commit names or other details about individuals. Unverified records must not enter this
  public repository.

## Ways to help

- **Data sources** — document public or official sources such as court portals, government animal
  abuser registries and agency data in the United States, China or India, the countries in
  [IROPO's scope](README.md#scope-the-united-states-and-beyond). Use the [data source form](https://github.com/the-robots/iropo.org/issues/new?template=data-source.yml).
- **Corrections** — report wrong numbers, names or ORI links with the
  [correction form](https://github.com/the-robots/iropo.org/issues/new?template=correction.yml).
- **Pipeline** — add importers, improve parsing and matching, or extend validation in [`pipeline/`](pipeline).
- **Website** — improve pages, charts, accessibility and explanations in [`src/`](src).
- **Policy and legal** — review the schema, verification and correction workflows.

## Development setup

Requirements: Node.js 22.12+ (see `.nvmrc`), Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
npm install
npm run dev            # website at http://localhost:4321

cd pipeline
uv sync
uv run iropo-data all  # fetch FBI data, rebuild data/processed, validate
```

No API key is needed. If you have an [api.data.gov key](https://api.data.gov/signup/), copy
`.env.example` to `.env`, set `FBI_API_KEY`, and export it before running the pipeline.

### Checks to run before opening a pull request

```bash
npm run check && npm run build            # website
cd pipeline && uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run iropo-data validate
```

CI runs the same checks on every pull request.

## Working with data

- The website reads only `data/processed/`. Change it by changing the pipeline and re-running
  `uv run iropo-data build`, not by editing the files by hand.
- Hand-maintained inputs live in `data/curated/` and must validate against the schemas in `data/schema/`.
- Every dataset must record where it came from. Keep URLs, retrieval dates and checksums intact.
- The monthly **Refresh FBI data** workflow opens a pull request with new data. Review the summary
  and spot-check a few state pages before merging.

## Opening issues and pull requests

- Use issues to document bugs, source leads, open questions or roadmap suggestions.
- Keep pull requests focused and explain what changed and why.
- Include basic validation steps in the pull request description.

## Handling sensitive subject matter

Please be careful when proposing or handling information about identifiable people:

- prefer public, official and reviewable sources;
- preserve source context and provenance;
- prioritize accuracy over speed;
- raise concerns if information appears unverifiable, outdated or legally sensitive.
