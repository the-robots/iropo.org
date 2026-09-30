import datetime as dt
import json

import pytest

from iropo_pipeline import config
from iropo_pipeline.build import _dumps, publishable
from iropo_pipeline.validate import validate_all


def record(**overrides):
    base = {
        "status": "verified",
        "case": {"disposition": "convicted"},
        "sources": [{"type": "court_record"}],
        "verification": {"reviewers": ["alice", "bob"]},
        "listing": {},
    }
    base.update(overrides)
    return base


def test_publication_gate_requires_verified_adjudicated_official_records():
    today = dt.date(2026, 9, 30)
    assert publishable(record(), today)
    assert not publishable(record(status="in_review"), today)
    assert not publishable(record(status="disputed"), today)
    assert not publishable(record(case={"disposition": "charged"}), today)
    assert not publishable(record(sources=[{"type": "news_report"}]), today)
    assert not publishable(record(listing={"removed_at": "2026-01-01T00:00:00Z"}), today)


def test_publication_gate_requires_two_reviewers_and_unexpired_listing():
    today = dt.date(2026, 9, 30)
    assert not publishable(record(verification={"reviewers": ["alice"]}), today)
    assert not publishable(record(verification={"reviewers": ["alice", "Alice"]}), today)
    assert not publishable(record(listing={"expires_at": "2026-09-30"}), today)
    assert publishable(record(listing={"expires_at": "2027-01-01"}), today)


def test_dumps_keeps_scalar_arrays_on_one_line():
    text = _dumps({"years": [2020, 2021], "nested": {"a": [{"b": 1}, {"c": [1, None]}]}})
    assert '"years": [2020,2021]' in text
    assert json.loads(text) == {
        "years": [2020, 2021],
        "nested": {"a": [{"b": 1}, {"c": [1, None]}]},
    }


@pytest.mark.skipif(
    not (config.PROCESSED_DIR / "states.json").exists(), reason="processed data not built"
)
def test_committed_datasets_match_schemas():
    assert validate_all() == []
