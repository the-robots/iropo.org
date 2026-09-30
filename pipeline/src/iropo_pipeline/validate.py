"""Validate processed and curated datasets against the JSON Schemas in ``data/schema``."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from iropo_pipeline import config


def _schema(name: str) -> Draft202012Validator:
    schema = json.loads((config.SCHEMA_DIR / name).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _errors(validator: Draft202012Validator, payload, label: str) -> list[str]:
    return [
        f"{label}: {'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(payload)
    ][:20]


def validate_all(processed: Path | None = None, curated: Path | None = None) -> list[str]:
    processed = processed or config.PROCESSED_DIR
    curated = curated or config.CURATED_DIR
    problems: list[str] = []

    series = _schema("series.schema.json")
    for name in ("national.json", "states.json"):
        path = processed / name
        if not path.exists():
            problems.append(f"{name}: missing (run `iropo-data build`)")
            continue
        problems += _errors(series, json.loads(path.read_text()), name)

    agencies = _schema("agencies.schema.json")
    agency_files = sorted((processed / "agencies").glob("*.json"))
    if len(agency_files) < 51:
        problems.append(f"agencies/: expected 51 state files, found {len(agency_files)}")
    for path in agency_files:
        problems += _errors(agencies, json.loads(path.read_text()), f"agencies/{path.name}")

    registries = _schema("official-registries.schema.json")
    for path in (curated / "official-registries.json", processed / "official-registries.json"):
        if path.exists():
            problems += _errors(registries, json.loads(path.read_text()), str(path.name))

    record = _schema("registry-record.schema.json")
    records_path = curated / "registry-records.json"
    if records_path.exists():
        for index, item in enumerate(json.loads(records_path.read_text())):
            problems += _errors(record, item, f"registry-records.json[{index}]")
    published_path = processed / "registry.json"
    if published_path.exists():
        for index, item in enumerate(json.loads(published_path.read_text()).get("records", [])):
            problems += _errors(record, item, f"registry.json[{index}]")
            if item.get("status") != "verified":
                problems.append(f"registry.json[{index}]: unverified record would be published")
    return problems
