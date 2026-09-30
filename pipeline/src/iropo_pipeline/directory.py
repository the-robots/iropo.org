"""Normalize the FBI agency directory returned by ``/agency/byStateAbbr/{state}``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DIRECTORY_TYPES = {
    "City": "city",
    "County": "county",
    "University or College": "university",
    "Other": "other",
    "Other State Agency": "other_state",
    "State Police": "state_police",
    "Tribal": "tribal",
    "Federal": "federal",
}


@dataclass(frozen=True)
class DirectoryAgency:
    ori: str
    name: str
    type: str
    state: str
    counties: str | None
    latitude: float | None
    longitude: float | None
    nibrs: bool
    nibrs_since: str | None


def _title_county(value: str | None) -> str | None:
    if not value or str(value).strip().upper() in {"", "NOT SPECIFIED", "NONE", "N/A"}:
        return None
    parts = [p.strip() for p in str(value).split(",") if p.strip()]
    return ", ".join(
        " ".join(
            w.capitalize() if not w.startswith("MC") else "Mc" + w[2:].capitalize()
            for w in p.split()
        )
        for p in parts
    )


def _coord(value) -> float | None:
    try:
        return round(float(value), 5) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_directory(payload: dict, state: str) -> list[DirectoryAgency]:
    """Flatten the county-keyed payload and de-duplicate agencies by ORI."""
    agencies: dict[str, DirectoryAgency] = {}
    for entries in payload.values():
        for raw in entries or []:
            ori = str(raw.get("ori") or "").strip().upper()
            if not ori or ori in agencies:
                continue
            agencies[ori] = DirectoryAgency(
                ori=ori,
                name=" ".join(str(raw.get("agency_name") or ori).split()),
                type=DIRECTORY_TYPES.get(raw.get("agency_type_name"), "other"),
                state=(raw.get("state_abbr") or state).upper(),
                counties=_title_county(raw.get("counties")),
                latitude=_coord(raw.get("latitude")),
                longitude=_coord(raw.get("longitude")),
                nibrs=bool(raw.get("is_nibrs")),
                nibrs_since=(raw.get("nibrs_start_date") or None),
            )
    return sorted(agencies.values(), key=lambda a: (a.name.lower(), a.ori))


def load_directory(path: Path, state: str) -> list[DirectoryAgency]:
    return parse_directory(json.loads(path.read_text()), state)
