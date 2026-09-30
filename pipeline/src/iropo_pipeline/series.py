"""Turn CDE ``/nibrs/{national|state}/720`` responses into monthly and annual series."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Month:
    month: str  # YYYY-MM
    offenses: int | None
    clearances: int | None
    coverage_pct: float | None
    population: int | None
    covered_population: int | None


@dataclass(frozen=True)
class Year:
    year: int
    months_reported: int
    offenses: int | None
    clearances: int | None
    coverage_pct: float
    population: int | None
    covered_population: int | None
    rate_per_100k: float | None
    clearance_rate: float | None


def _series(block: dict, suffix: str, exclude_us: bool) -> dict[str, float | None]:
    for key, values in (block or {}).items():
        if not key.endswith(suffix):
            continue
        if exclude_us and key.startswith("United States"):
            continue
        return values or {}
    return {}


def _place(block: dict, exclude_us: bool) -> dict:
    for key, values in (block or {}).items():
        if exclude_us and key == "United States":
            continue
        return values or {}
    return {}


def _ym(key: str) -> str:
    month, year = key.split("-")
    return f"{year}-{month}"


def latest_complete_year(payload: dict, settle_months: int = 6) -> int:
    """Latest calendar year whose monthly data has had time to settle.

    ``cde_properties.max_data_date`` is the month of the latest refresh, whose own data (and that
    of the months just before it) is still arriving. A year is treated as complete once
    ``settle_months`` have passed after it ends. Callers should also cap the result at the newest
    year with published annual tables.
    """
    raw = ((payload.get("cde_properties") or {}).get("max_data_date") or {}).get("UCR", "")
    month, _, year = raw.partition("/")
    if not (month.isdigit() and year.isdigit()):
        raise ValueError(f"Unexpected max_data_date: {raw!r}")
    return int(year) - 1 if int(month) >= settle_months else int(year) - 2


def parse_monthly(payload: dict, national: bool) -> list[Month]:
    exclude_us = not national
    offenses = payload.get("offenses") or {}
    actual_offenses = _series(offenses.get("actuals"), " Offenses", exclude_us)
    actual_clearances = _series(offenses.get("actuals"), " Clearances", exclude_us)
    coverage = _place(
        (payload.get("tooltips") or {}).get("Percent of Population Coverage"), exclude_us
    )
    populations = payload.get("populations") or {}
    population = _place(populations.get("population"), exclude_us)
    covered = _place(populations.get("participated_population"), exclude_us)

    months: list[Month] = []
    for key in sorted(set(actual_offenses) | set(population), key=_ym):
        pct = coverage.get(key)
        has_data = pct is not None and pct > 0 and (covered.get(key) or 0) > 0
        months.append(
            Month(
                month=_ym(key),
                offenses=int(actual_offenses.get(key) or 0) if has_data else None,
                clearances=int(actual_clearances.get(key) or 0) if has_data else None,
                coverage_pct=round(float(pct), 2) if pct is not None else None,
                population=int(population[key]) if population.get(key) else None,
                covered_population=int(covered[key]) if covered.get(key) else None,
            )
        )
    return months


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def annualize(months: list[Month], first_year: int, last_year: int) -> list[Year]:
    by_year: dict[int, list[Month]] = {}
    for month in months:
        by_year.setdefault(int(month.month[:4]), []).append(month)
    years: list[Year] = []
    for year in range(first_year, last_year + 1):
        entries = by_year.get(year, [])
        reported = [m for m in entries if m.offenses is not None]
        offenses = sum(m.offenses for m in reported) if reported else None
        clearances = sum(m.clearances or 0 for m in reported) if reported else None
        coverage = sum(m.coverage_pct or 0 for m in entries) / 12
        population = _mean([m.population for m in entries if m.population])
        covered = _mean([m.covered_population or 0 for m in reported])
        rate = offenses / covered * 100_000 if offenses is not None and covered else None
        years.append(
            Year(
                year=year,
                months_reported=len(reported),
                offenses=offenses,
                clearances=clearances,
                coverage_pct=round(coverage, 1),
                population=round(population) if population else None,
                covered_population=round(covered) if covered else None,
                rate_per_100k=round(rate, 2) if rate is not None else None,
                clearance_rate=round(clearances / offenses, 3) if offenses else None,
            )
        )
    return years
