"""Command-line entry point: ``iropo-data {fetch,build,validate,all}``."""

from __future__ import annotations

import argparse
import sys

from iropo_pipeline.states import STATES, lookup_state


def _states(value: str | None):
    if not value:
        return None
    resolved = []
    for token in value.split(","):
        state = lookup_state(token.strip())
        if state is None:
            raise argparse.ArgumentTypeError(f"Unknown state: {token}")
        resolved.append(state)
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="iropo-data", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Download raw FBI data into data/cache")
    fetch.add_argument("--states", type=_states, help="Comma-separated states (default: all)")
    fetch.add_argument("--refresh", action="store_true", help="Re-download cached files")
    fetch.add_argument("--through-year", type=int, help="Last calendar year to request")

    sub.add_parser("build", help="Build data/processed from the cache and curated files")
    sub.add_parser("validate", help="Validate data/processed and data/curated against schemas")

    everything = sub.add_parser("all", help="fetch + build + validate")
    everything.add_argument("--refresh", action="store_true")

    args = parser.parse_args(argv)

    if args.command in ("fetch", "all"):
        from iropo_pipeline.cde import CdeClient
        from iropo_pipeline.fetch import fetch_all

        fetch_all(
            CdeClient.from_env(),
            states=getattr(args, "states", None) or STATES,
            refresh=args.refresh,
            through_year=getattr(args, "through_year", None),
        )
    if args.command in ("build", "all"):
        from iropo_pipeline.build import build_all

        build_all()
    if args.command in ("validate", "all"):
        from iropo_pipeline.validate import validate_all

        problems = validate_all()
        for problem in problems:
            print(f"INVALID: {problem}", file=sys.stderr)
        if problems:
            return 1
        print("All datasets are valid.")
    return 0
