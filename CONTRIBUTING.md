# Contributing to IROPO

Thank you for considering a contribution to this planning-stage repository.

## Before you start

- Read the project overview in [`README.md`](README.md).
- Follow the community expectations in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- Do not commit API keys, tokens, account identifiers, or personal contact details.

## Ways to help

Contributions that are especially useful right now include:

- documenting public or official data sources
- improving the prototype data scripts
- proposing data schema or verification approaches
- suggesting site architecture, workflow, or contributor-process improvements
- clarifying documentation and roadmap items

## Opening issues and pull requests

- Use issues to document bugs, source leads, open questions, or roadmap suggestions.
- Keep pull requests focused and explain what changed and why.
- When changing scripts or configuration, include basic validation steps in the PR description.

## Handling sensitive subject matter

Please be careful when proposing or handling information about identifiable people:

- prefer public, official, and reviewable sources
- preserve source context and provenance
- prioritize accuracy over speed
- raise concerns if information appears unverifiable, outdated, or legally sensitive

## Development notes

The current Python prototypes use dependencies listed in [`requirements.txt`](requirements.txt) and expect `FBI_API_KEY` to be provided through the environment when API calls are needed.
