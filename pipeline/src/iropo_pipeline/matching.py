"""Link FBI table rows (which only carry agency names) to ORIs in the FBI agency directory.

Matching happens within a state and year, in tiers from strictest to loosest, and every ORI can be
claimed by at most one table row per state-year:

1. ``exact`` - identical names after case/punctuation normalization
   (``Highway Patrol, Altadena Area Office`` = ``Highway Patrol: Altadena Area Office``).
2. ``normalized`` - identical once generic words such as "Police Department" or
   "Sheriff's Office" are removed (``Aberdeen`` = ``Aberdeen Police Department``).
3. ``tokens`` - the same set of words in a different order.

Ties are broken by agency role (a plain county name maps to the sheriff, "... Police Department"
to the police department) and by NIBRS participation. Rows that stay ambiguous are left unmatched.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Iterable

from iropo_pipeline.directory import DirectoryAgency
from iropo_pipeline.tables import AgencyTableRow

COMPATIBLE_TYPES = {
    "city": {"city"},
    "metro_county": {"county"},
    "nonmetro_county": {"county"},
    "university": {"university", "other", "other_state"},
    "tribal": {"tribal", "other"},
    "state_police": {"state_police", "other_state", "other"},
    "other": {"other", "other_state", "state_police", "university", "tribal", "county", "city"},
}

_GENERIC_PHRASES = [
    "department of public safety",
    "public safety department",
    "police department",
    "police dept",
    "sheriffs office",
    "sheriff office",
    "sheriffs department",
    "sheriff department",
    "marshals office",
    "police",
]
_STOPWORDS = {"the", "of", "at", "and"}
_COUNTY_WORDS = {"county", "parish", "borough"}


def canonical(name: str) -> str:
    text = name.lower().replace("&", " and ").replace("'", "").replace("\u2019", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _strip_generic(text: str) -> str:
    for phrase in _GENERIC_PHRASES:
        text = re.sub(rf"\b{phrase}\b", " ", text)
    return " ".join(text.split())


def key_exact(name: str, _type: str) -> str:
    return canonical(name)


def key_normalized(name: str, agency_type: str) -> str:
    words = _strip_generic(canonical(name)).split()
    if agency_type in {"metro_county", "nonmetro_county", "county"}:
        words = [w for w in words if w not in _COUNTY_WORDS]
    return " ".join(w for w in words if w not in _STOPWORDS)


def key_tokens(name: str, agency_type: str) -> str:
    return " ".join(sorted(set(key_normalized(name, agency_type).split())))


TIERS: list[tuple[str, Callable[[str, str], str]]] = [
    ("exact", key_exact),
    ("normalized", key_normalized),
    ("tokens", key_tokens),
]


def _preference(row: AgencyTableRow, agency: DirectoryAgency) -> tuple:
    row_words = set(canonical(row.name).split())
    agency_words = set(canonical(agency.name).split())
    if "police" in row_words:
        role = "police" in agency_words
    elif (
        "sheriff" in row_words
        or "sheriffs" in row_words
        or row.agency_type in {"metro_county", "nonmetro_county"}
    ):
        role = bool({"sheriff", "sheriffs"} & agency_words)
    elif row.agency_type == "city":
        role = "police" in agency_words
    else:
        role = True
    return (role, agency.nibrs)


def match_rows(
    rows: Iterable[AgencyTableRow], directory: Iterable[DirectoryAgency]
) -> dict[AgencyTableRow, tuple[str, str]]:
    """Return ``{row: (ori, method)}`` for rows that could be linked to the directory."""
    by_state: dict[str, list[DirectoryAgency]] = defaultdict(list)
    for agency in directory:
        by_state[agency.state].append(agency)

    groups: dict[tuple[str, int], list[AgencyTableRow]] = defaultdict(list)
    for row in rows:
        groups[(row.state, row.year)].append(row)

    matches: dict[AgencyTableRow, tuple[str, str]] = {}
    for (state, _year), group in groups.items():
        agencies = by_state.get(state, [])
        used: set[str] = set()
        for method, keyer in TIERS:
            index: dict[str, list[DirectoryAgency]] = defaultdict(list)
            for agency in agencies:
                index[keyer(agency.name, agency.type)].append(agency)
            for row in group:
                if row in matches:
                    continue
                key = keyer(row.name, row.agency_type)
                if not key:
                    continue
                candidates = [
                    a
                    for a in index.get(key, [])
                    if a.ori not in used and a.type in COMPATIBLE_TYPES.get(row.agency_type, set())
                ]
                if not candidates:
                    continue
                ranked = sorted(candidates, key=lambda a: _preference(row, a), reverse=True)
                if len(ranked) > 1 and _preference(row, ranked[0]) == _preference(row, ranked[1]):
                    continue  # still ambiguous - leave for a looser tier or unmatched
                matches[row] = (ranked[0].ori, method)
                used.add(ranked[0].ori)
    return matches
