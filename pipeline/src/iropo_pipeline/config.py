"""Paths and constants shared across the pipeline."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(os.environ.get("IROPO_REPO_ROOT", Path(__file__).resolve().parents[3]))
DATA_DIR = REPO_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DIR = DATA_DIR / "processed"
CURATED_DIR = DATA_DIR / "curated"
SCHEMA_DIR = DATA_DIR / "schema"
LEGACY_DIR = DATA_DIR / "raw" / "legacy"

# NIBRS offense code 720 = Animal Cruelty (a Group A offense since January 2016).
ANIMAL_CRUELTY_CODE = "720"

# Monthly CDE series start the year animal cruelty became a NIBRS Group A offense.
SERIES_FIRST_YEAR = 2016

# The FBI publishes "Offense Type by Agency" tables on the CDE downloads page from 2020 onward.
TABLE_FIRST_YEAR = 2020

# Years whose agency tables ship as a single national workbook instead of one file per state.
COMBINED_TABLE_FIRST_YEAR = 2024

CONTACT_URL = "https://iropo.org"
USER_AGENT = f"iropo-data-pipeline/0.2 (+{CONTACT_URL})"
