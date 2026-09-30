"""Download raw source data into ``data/cache`` and record provenance in a manifest."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from iropo_pipeline import config
from iropo_pipeline.cde import CdeClient, NotAvailable
from iropo_pipeline.states import STATES, State

MANIFEST_PATH = config.CACHE_DIR / "manifest.json"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Manifest:
    """Tracks where every cached file came from and when it was retrieved."""

    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = MANIFEST_PATH) -> Manifest:
        if path.exists():
            return cls(json.loads(path.read_text()))
        return cls()

    def save(self, path: Path = MANIFEST_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(sorted(self.entries.items())), indent=2) + "\n")

    def record(self, file: Path, url: str, sha256: str) -> None:
        self.entries[relative(file)] = {
            "url": url,
            "retrieved_at": utc_now(),
            "sha256": sha256,
            "bytes": file.stat().st_size,
        }

    def get(self, file: Path) -> dict[str, Any] | None:
        return self.entries.get(relative(file))


def relative(file: Path) -> str:
    return file.resolve().relative_to(config.CACHE_DIR.resolve()).as_posix()


def agencies_path(state: State) -> Path:
    return config.CACHE_DIR / "cde" / "agencies" / f"{state.abbr}.json"


def series_path(abbr: str) -> Path:
    return config.CACHE_DIR / "cde" / f"nibrs-{config.ANIMAL_CRUELTY_CODE}" / f"{abbr}.json"


def table_key(year: int, kind: str) -> str:
    if kind == "agencies":
        name = "statesAndFederal" if year >= config.COMBINED_TABLE_FIRST_YEAR else "stateTables"
    elif kind == "offenders":
        name = "offenders"
    else:
        raise ValueError(f"Unknown table kind: {kind}")
    return f"nibrs/tables/{year}/{name}.zip"


def table_path(year: int, kind: str) -> Path:
    return config.CACHE_DIR / "fbi" / "nibrs-tables" / f"{year}-{kind}.zip"


def _save_json(file: Path, payload: Any, url: str, manifest: Manifest) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, sort_keys=True).encode()
    file.write_bytes(body)
    manifest.record(file, url, hashlib.sha256(body).hexdigest())


def fetch_agency_directories(
    client: CdeClient, manifest: Manifest, states: list[State], refresh: bool, log=print
) -> None:
    for state in states:
        file = agencies_path(state)
        if file.exists() and not refresh:
            continue
        path = f"agency/byStateAbbr/{state.abbr}"
        log(f"  agencies {state.abbr}")
        _save_json(file, client.get_json(path), client.url_for(path), manifest)


def fetch_series(
    client: CdeClient,
    manifest: Manifest,
    states: list[State],
    refresh: bool,
    through_year: int,
    log=print,
) -> None:
    params = {
        "type": "counts",
        "from": f"01-{config.SERIES_FIRST_YEAR}",
        "to": f"12-{through_year}",
    }
    targets: list[tuple[str, str]] = [("US", f"nibrs/national/{config.ANIMAL_CRUELTY_CODE}")]
    targets += [(s.abbr, f"nibrs/state/{s.abbr}/{config.ANIMAL_CRUELTY_CODE}") for s in states]
    for abbr, path in targets:
        file = series_path(abbr)
        if file.exists() and not refresh:
            continue
        log(f"  animal-cruelty series {abbr}")
        _save_json(file, client.get_json(path, params), client.url_for(path, params), manifest)


def fetch_tables(
    client: CdeClient, manifest: Manifest, years: list[int], refresh: bool, log=print
) -> None:
    for year in years:
        for kind in ("agencies", "offenders"):
            file = table_path(year, kind)
            if file.exists() and not refresh:
                continue
            key = table_key(year, kind)
            try:
                url = client.signed_url(key)
                log(f"  NIBRS tables {year} {kind}")
                digest = client.download(url, file)
            except NotAvailable:
                log(f"  NIBRS tables {year} {kind}: not published, skipping")
                continue
            manifest.record(
                file, f"https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads ({key})", digest
            )


def fetch_all(
    client: CdeClient,
    *,
    states: list[State] | None = None,
    refresh: bool = False,
    through_year: int | None = None,
    log=print,
) -> Manifest:
    states = states or STATES
    through_year = through_year or dt.date.today().year
    manifest = Manifest.load()
    log(f"Fetching from {client.base_url} ({'API key' if client.api_key else 'no key'})")
    try:
        fetch_agency_directories(client, manifest, states, refresh, log)
        fetch_series(client, manifest, states, refresh, through_year, log)
        fetch_tables(
            client, manifest, list(range(config.TABLE_FIRST_YEAR, through_year + 1)), refresh, log
        )
    finally:
        manifest.save()
    return manifest
