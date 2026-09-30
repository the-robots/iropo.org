"""Cross-check the legacy agency spreadsheets against today's FBI agency directory.

The ``localAndStateAgencies-*.xlsx`` files were transcribed (via OCR) from the 1977 NLETS
directory of criminal justice agencies (NCJRS document 75873). Many ORIs are still valid, but the
transcription introduced errors such as ``I`` for ``1`` or ``O``/``D`` for ``0``. Each legacy ORI is
classified as:

* ``current`` - the ORI exists in today's FBI directory for that state.
* ``likely_ocr_error`` - swapping look-alike characters yields exactly one current ORI whose name
  or county agrees with the legacy entry.
* ``federal`` - a federal field office; these are not part of the state directories.
* ``not_found`` - no current agency could be identified (renamed, merged or defunct agencies).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import openpyxl

from iropo_pipeline.directory import DirectoryAgency

LEGACY_FILES = {
    "NC": "localAndStateAgencies-NC.xlsx",
    "ND": "localAndStateAgencies-ND.xlsx",
    "NY": "localAndStateAgencies-NY.xlsx",
}
SHEET_STATE_WORDS = {"NC": "NORTH CAROLINA", "ND": "NORTH DAKOTA", "NY": "NEW"}

ORI_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{7}$")
LOOKALIKES: dict[str, str] = {
    "0": "ODQ",
    "O": "0DQ",
    "D": "0O",
    "Q": "0O",
    "1": "IL",
    "I": "1L",
    "L": "1I",
    "5": "S",
    "S": "5",
    "8": "B",
    "B": "8",
    "2": "Z",
    "Z": "2",
    "6": "G",
    "G": "6",
}


@dataclass(frozen=True)
class LegacyAgency:
    state: str
    sheet: str
    agency: str
    city: str | None
    county: str | None
    ori: str


@dataclass(frozen=True)
class CrosswalkRow:
    legacy: LegacyAgency
    status: str
    current: DirectoryAgency | None
    name_consistent: bool | None = None


_GENERIC_WORDS = {
    "PD",
    "POLICE",
    "DEPARTMENT",
    "DEPT",
    "SHERIFF",
    "SHERIFFS",
    "OFFICE",
    "COUNTY",
    "CITY",
    "TOWN",
    "VILLAGE",
    "TOWNSHIP",
    "STATE",
    "PUBLIC",
    "SAFETY",
    "THE",
    "AND",
    "OF",
    "DIVISION",
}


def _words(*values: str | None) -> set[str]:
    words: set[str] = set()
    for value in values:
        for word in re.findall(r"[A-Z]{3,}", (value or "").upper().replace("'", "")):
            if word not in _GENERIC_WORDS:
                words.add(word)
    return words


def names_consistent(legacy: LegacyAgency, current: DirectoryAgency) -> bool:
    """True when the legacy name, city or county shares a distinctive word with the match."""
    return bool(
        _words(legacy.agency, legacy.city, legacy.county) & _words(current.name, current.counties)
    )


def _text(value) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def read_legacy_workbook(path: Path, state: str) -> list[LegacyAgency]:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    agencies: list[LegacyAgency] = []
    try:
        for sheet in workbook.worksheets:
            # The ND workbook also carries copies of the New York sheets; only read this state's.
            if SHEET_STATE_WORDS[state] not in sheet.title.upper().replace("NEWYORK", "NEW YORK"):
                continue
            columns: dict[str, int] | None = None
            for row in sheet.iter_rows(values_only=True):
                cells = [_text(v) for v in row]
                labels = [(c or "").upper().replace("0RI", "ORI") for c in cells]
                if columns is None:
                    if "AGENCY" in labels and "ORI" in labels:
                        columns = {
                            name: labels.index(name)
                            for name in ("AGENCY", "ADDRESS", "COUNTY", "ORI")
                            if name in labels
                        }
                    continue
                ori = (cells[columns["ORI"]] or "").upper().replace(" ", "")
                name = cells[columns["AGENCY"]]
                if not ori or not name or ori in {"N/A", "ORI"}:
                    continue
                agencies.append(
                    LegacyAgency(
                        state=state,
                        sheet=sheet.title.strip(),
                        agency=name,
                        city=cells[columns["ADDRESS"]] if "ADDRESS" in columns else None,
                        county=cells[columns["COUNTY"]] if "COUNTY" in columns else None,
                        ori=ori,
                    )
                )
    finally:
        workbook.close()
    return agencies


def lookalike_candidates(ori: str, max_swaps: int = 2) -> set[str]:
    """All ORIs reachable by swapping up to ``max_swaps`` look-alike characters."""
    found: set[str] = set()
    positions = [i for i, ch in enumerate(ori) if ch in LOOKALIKES]
    for swaps in range(1, max_swaps + 1):
        for chosen in combinations(positions, swaps):
            variants = [ori]
            for pos in chosen:
                variants = [
                    v[:pos] + alt + v[pos + 1 :] for v in variants for alt in LOOKALIKES[v[pos]]
                ]
            found.update(variants)
    found.discard(ori)
    return found


def crosswalk(legacy: list[LegacyAgency], directory: list[DirectoryAgency]) -> list[CrosswalkRow]:
    current = {a.ori: a for a in directory}
    rows: list[CrosswalkRow] = []
    for agency in legacy:
        if agency.ori in current:
            match = current[agency.ori]
            rows.append(CrosswalkRow(agency, "current", match, names_consistent(agency, match)))
            continue
        if "FEDERAL" in agency.sheet.upper():
            # Federal field offices are not part of the state directories.
            rows.append(CrosswalkRow(agency, "federal", None))
            continue
        matches = sorted(
            c
            for c in lookalike_candidates(agency.ori)
            if c in current and names_consistent(agency, current[c])
        )
        if len(matches) == 1:
            rows.append(CrosswalkRow(agency, "likely_ocr_error", current[matches[0]], True))
        else:
            rows.append(CrosswalkRow(agency, "not_found", None))
    return rows


def is_valid_ori(value: str) -> bool:
    return bool(ORI_PATTERN.match(value))
