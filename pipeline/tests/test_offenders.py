from iropo_pipeline import config
from iropo_pipeline.offenders import dimension_for, parse_offender_sheet, parse_offender_workbook

LEGACY_2020 = config.LEGACY_DIR / "nibrs-2020" / "offenders"


def test_dimension_detection_prefers_adult_juvenile_table():
    name = "Offenders_Adult_and_Juvenile_Age_Category_by_Offense_Category_2020.xls.xlsx"
    assert dimension_for(name) == "age_category"
    assert dimension_for("NIBRS_Table_9_Offenders_Age_by_Offense_Category_2025.xlsx") == "age"
    assert dimension_for("NIBRS_Table_10_Offenders_Sex_by_Offense_Category_2025.xlsx") == "sex"
    assert dimension_for("readme.txt") is None


def test_legacy_2020_tables_match_published_totals():
    suffix = "by_Offense_Category_2020.xls.xlsx"
    files = {
        "age_category": f"Offenders_Adult_and_Juvenile_Age_Category_{suffix}",
        "age": f"Offenders_Age_{suffix}",
        "sex": f"Offenders_Sex_{suffix}",
        "race": f"Offenders_Race_{suffix}",
    }
    for dimension, name in files.items():
        table = parse_offender_workbook(LEGACY_2020 / name, dimension)
        cruelty = table["animal_cruelty"]
        assert cruelty["total"] == 10414, dimension
        assert sum(v for k, v in cruelty.items() if k != "total") == 10414, dimension
        assert table["all_offenses"]["total"] == 7173072
    sex = parse_offender_workbook(LEGACY_2020 / files["sex"], "sex")["animal_cruelty"]
    assert sex == {"total": 10414, "male": 5964, "female": 3609, "unknown": 841}


def test_header_on_row_above_labels_2025_layout():
    rows = [
        ("Table 10",),
        ("Offense Category", "Total Offenders1", "Sex", None, None),
        (None, None, "Male", "Female", "Unknown Sex"),
        ("Total", 100, 60, 30, 10),
        ("Animal Cruelty", 10, 5, 4, 1),
    ]
    parsed = parse_offender_sheet(rows, "sex")
    assert parsed["animal_cruelty"] == {"total": 10, "male": 5, "female": 4, "unknown": 1}


def test_age_labels_with_unicode_minus():
    rows = [
        (None, None, "10 and Under", "11\u221215", "66 and Over", "Unknown Age"),
        ("Total", 20, 1, 2, 3, 14),
        ("Animal Cruelty", 6, 0, 1, 2, 3),
    ]
    parsed = parse_offender_sheet(rows, "age")
    assert parsed["animal_cruelty"] == {"total": 6, "0-10": 0, "11-15": 1, "66+": 2, "unknown": 3}
