from iropo_pipeline.tables import (
    SimpleCell,
    _is_agency_workbook,
    normalize_agency_type,
    normalize_header,
    parse_int,
    parse_worksheet_rows,
    state_from_filename,
    state_from_title,
)


def cells(*values, indent=None):
    indent = indent or {}
    return tuple(SimpleCell(v, indent.get(i, 0.0)) for i, v in enumerate(values))


def test_normalize_header_strips_footnotes_and_line_breaks():
    assert normalize_header("Animal \nCruelty") == "animal cruelty"
    assert normalize_header("Population1") == "population"
    assert normalize_header("Total\nOffenses") == "total offenses"
    assert normalize_header("Imper-\nsonation") == "impersonation"
    assert normalize_header("State/Territory") == "state territory"
    assert normalize_header(None) == ""


def test_agency_types_cover_both_eras():
    assert normalize_agency_type("Cities") == "city"
    assert normalize_agency_type("City") == "city"
    assert normalize_agency_type("Metropolitan Counties") == "metro_county"
    assert normalize_agency_type("Nonmetropolitan County") == "nonmetro_county"
    assert normalize_agency_type("University or College") == "university"
    assert normalize_agency_type("1Population figures are published only for cities") is None


def test_parse_int_handles_excel_values():
    assert parse_int(12) == 12
    assert parse_int(12.0) == 12
    assert parse_int("1,835") == 1835
    assert parse_int("") is None
    assert parse_int(None) is None
    assert parse_int("n/a") is None


def test_state_from_filename():
    assert state_from_filename("x/North_Carolina_Offense_Type_by_Agency_2023.xlsx") == "NC"
    assert state_from_filename("District_of_Columbia_Offense_Type_by_Agency_2020.xls") == "DC"
    assert state_from_filename("Guam_Offense_Type_by_Agency_2023.xlsx") is None
    assert state_from_filename("NIBRS_United_States_Offense_Type_by_State_2025.xlsx") is None


def test_two_row_header_with_groups_and_forward_filled_types():
    rows = [
        cells("North Carolina"),
        cells(
            "Agency Type", "Agency Name", "Population1", "Total Offenses", "Crimes Against Society"
        ),
        cells(None, None, None, None, "Animal  Cruelty"),
        cells("Cities", "Aberdeen", 9670, 1070, 4),
        cells(None, "Ahoskie", 4554, 623, 1),
        cells("Other", "State Park Rangers:", None, None, None),
        cells(None, "Elk Knob", None, 0, 0, indent={1: 3.0}),
        cells(None, "Kerr Lake", None, 48, 2, indent={1: 3.0}),
        cells(None, "WakeMed Campus Police", None, 820, 0),
        cells("1Population figures are published only for the cities."),
    ]
    parsed = list(parse_worksheet_rows(rows, 2023, "NC"))
    assert [(r.agency_type, r.name, r.animal_cruelty) for r in parsed] == [
        ("city", "Aberdeen", 4),
        ("city", "Ahoskie", 1),
        ("other", "State Park Rangers, Elk Knob", 0),
        ("other", "State Park Rangers, Kerr Lake", 2),
        ("other", "WakeMed Campus Police", 0),
    ]
    assert parsed[0].population == 9670
    assert parsed[0].total_offenses == 1070


def test_single_row_header_keeps_first_data_row():
    rows = [
        cells("Agency Type", "Agency Name", "Population1", "Total Offenses", "Animal Cruelty"),
        cells("Cities", "Aberdeen", 8576, 784, 0),
        cells(None, "Ahoskie", 4653, 548, 2),
    ]
    parsed = list(parse_worksheet_rows(rows, 2021, "NC"))
    assert [r.name for r in parsed] == ["Aberdeen", "Ahoskie"]
    assert all(r.agency_type == "city" for r in parsed)


def test_national_layout_uses_state_column_and_skips_territories():
    rows = [
        cells(
            "State/Territory", "Agency Type", "Agency Name", "Population2", "Total\nOffenses", None
        ),
        cells(None, None, None, None, None, "Animal \nCruelty"),
        cells("Alabama", "City", "Abbeville", 2375, 306, 1),
        cells("Guam", "Other", "Guam Police Department", None, 6542, 3),
        cells("Texas", "City", "University of Oklahoma, Tulsa5", None, 10, 0),
    ]
    parsed = list(parse_worksheet_rows(rows, 2025, None))
    assert [(r.state, r.name) for r in parsed] == [
        ("AL", "Abbeville"),
        ("TX", "University of Oklahoma, Tulsa"),  # footnote marker removed
    ]


def test_state_from_title_handles_misspelled_file_names():
    rows = [cells("PENNSYLVANIA"), cells("Offense Type"), cells("by Agency, 2021")]
    assert state_from_filename("Pennyslvania_Offense_Type_by_Agency_2021.xlsx") is None
    assert state_from_title(rows) == "PA"
    assert state_from_title([cells("Table 40"), cells("United States")]) is None


def test_workbook_selection_keeps_tribal_tables_only():
    assert _is_agency_workbook("NIBRS_United_States_Offense_Type_by_Federal_and_Tribal_2025.xlsx")
    assert not _is_agency_workbook("State Tables/Federal_Offense_Type_by_Agency_2021.xlsx")
    assert not _is_agency_workbook("United_States_Offense_Type_by_Agency_2023.xlsx")
    assert _is_agency_workbook("x/Pennyslvania_Offense_Type_by_Agency_2020.xls")


def test_federal_and_tribal_layout_keeps_tribal_rows_with_states():
    rows = [
        cells("Federal/State", "Agency Type", "Agency Name", "Total Offenses", None),
        cells(None, None, None, None, "Animal \nCruelty"),
        cells("Federal", "Federal", "Drug Enforcement Administration", 0, 0),
        cells("Washington", "Tribal", "Lummi Tribal", 120, 2),
    ]
    parsed = list(parse_worksheet_rows(rows, 2025, None))
    assert [(r.state, r.agency_type, r.name, r.animal_cruelty) for r in parsed] == [
        ("WA", "tribal", "Lummi Tribal", 2),
    ]
