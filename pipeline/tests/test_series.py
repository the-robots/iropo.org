import pytest

from iropo_pipeline.series import annualize, latest_complete_year, parse_monthly


def payload(max_date="09/2026"):
    return {
        "offenses": {
            "actuals": {
                "Ohio Offenses": {"01-2020": 5, "02-2020": 7, "01-2021": 0},
                "Ohio Clearances": {"01-2020": 1, "02-2020": 2, "01-2021": 0},
            },
            "rates": {"United States Offenses": {"01-2020": 0.5}},
        },
        "tooltips": {
            "Percent of Population Coverage": {
                "United States": {"01-2020": 60.0, "02-2020": 60.0, "01-2021": 70.0},
                "Ohio": {"01-2020": 80.0, "02-2020": 80.0},
            }
        },
        "populations": {
            "population": {
                "United States": {"01-2020": 330_000_000},
                "Ohio": {"01-2020": 1_000_000, "02-2020": 1_000_000, "01-2021": 1_000_000},
            },
            "participated_population": {
                "United States": {"01-2020": 200_000_000},
                "Ohio": {"01-2020": 800_000, "02-2020": 800_000, "01-2021": None},
            },
        },
        "cde_properties": {"max_data_date": {"UCR": max_date}},
    }


def test_latest_complete_year_waits_for_data_to_settle():
    assert latest_complete_year(payload("09/2026")) == 2025
    assert latest_complete_year(payload("06/2026")) == 2025
    # A December or early-year refresh still has incomplete recent months.
    assert latest_complete_year(payload("12/2026")) == 2025
    assert latest_complete_year(payload("03/2027")) == 2025
    with pytest.raises(ValueError):
        latest_complete_year(payload(""))


def test_state_series_ignores_national_keys_and_uncovered_months():
    months = parse_monthly(payload(), national=False)
    assert [m.month for m in months] == ["2020-01", "2020-02", "2021-01"]
    assert [m.offenses for m in months] == [5, 7, None]  # no coverage reported in 2021
    assert months[0].coverage_pct == 80.0


def test_annualize_sums_and_computes_rates():
    years = annualize(parse_monthly(payload(), national=False), 2020, 2021)
    first, second = years
    assert first.offenses == 12 and first.clearances == 3 and first.months_reported == 2
    assert first.rate_per_100k == pytest.approx(12 / 800_000 * 100_000, rel=1e-3)
    assert first.clearance_rate == 0.25
    assert first.coverage_pct == pytest.approx(160 / 12, abs=0.05)
    assert second.offenses is None and second.rate_per_100k is None
