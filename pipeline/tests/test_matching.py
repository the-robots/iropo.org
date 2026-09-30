from iropo_pipeline.directory import DirectoryAgency, parse_directory
from iropo_pipeline.matching import canonical, key_normalized, match_rows
from iropo_pipeline.tables import AgencyTableRow


def agency(ori, name, type_, state="GA", nibrs=True):
    return DirectoryAgency(
        ori=ori,
        name=name,
        type=type_,
        state=state,
        counties=None,
        latitude=None,
        longitude=None,
        nibrs=nibrs,
        nibrs_since=None,
    )


def row(name, type_, state="GA", year=2025, cruelty=1):
    return AgencyTableRow(
        year=year,
        state=state,
        agency_type=type_,
        name=name,
        population=None,
        total_offenses=10,
        animal_cruelty=cruelty,
    )


def test_canonical_ignores_case_and_punctuation():
    assert canonical("Highway Patrol: Altadena Area Office") == canonical(
        "Highway Patrol, Altadena Area Office"
    )
    assert canonical("Sheriff\u2019s Office") == "sheriffs office"
    assert key_normalized(
        "Liberty Township Police Department, Adams County", "city"
    ) == key_normalized("Liberty Township, Adams County", "city")


def test_county_rows_prefer_sheriff_unless_named_police():
    directory = [
        agency("GA0330000", "Cobb County Sheriff's Office", "county"),
        agency("GA0330200", "Cobb County Police Department", "county"),
    ]
    plain = row("Cobb", "metro_county")
    police = row("Cobb County Police Department", "metro_county")
    matches = match_rows([plain, police], directory)
    assert matches[police] == ("GA0330200", "exact")
    assert matches[plain] == ("GA0330000", "normalized")


def test_city_names_match_police_departments():
    directory = [agency("NC0630100", "Aberdeen Police Department", "city", state="NC")]
    table_row = row("Aberdeen", "city", state="NC")
    assert match_rows([table_row], directory)[table_row] == ("NC0630100", "normalized")


def test_type_and_state_must_be_compatible():
    directory = [agency("NC0630000", "Aberdeen County Sheriff's Office", "county", state="NC")]
    city_row = row("Aberdeen", "city", state="NC")
    other_state = row("Aberdeen", "metro_county", state="SC")
    assert match_rows([city_row, other_state], directory) == {}


def test_each_ori_is_claimed_once_per_state_year():
    directory = [agency("TX0000001", "Springfield Police Department", "city", state="TX")]
    first = row("Springfield", "city", state="TX")
    duplicate = row("Springfield Police", "city", state="TX")
    matches = match_rows([first, duplicate], directory)
    assert len(matches) == 1


def test_ambiguous_candidates_stay_unmatched():
    directory = [
        agency("PA0000001", "Liberty Township Police Department", "city", state="PA"),
        agency("PA0000002", "Liberty Township Police Department", "city", state="PA"),
    ]
    table_row = row("Liberty Township", "city", state="PA")
    assert match_rows([table_row], directory) == {}


def test_parse_directory_flattens_and_dedupes():
    payload = {
        "CASS": [
            {
                "ori": "ND0090200",
                "agency_name": "Fargo Police Department",
                "agency_type_name": "City",
                "counties": "CASS",
                "is_nibrs": True,
                "latitude": 46.9270034,
                "longitude": -97.25,
                "state_abbr": "ND",
                "nibrs_start_date": "1991-01-01",
            }
        ],
        "CASS, CLAY": [
            {
                "ori": "ND0090200",
                "agency_name": "Fargo Police Department",
                "agency_type_name": "City",
            }
        ],
        "MCKENZIE": [
            {
                "ori": "ND0270000",
                "agency_name": "McKenzie County Sheriff's Office",
                "agency_type_name": "County",
                "counties": "MCKENZIE",
                "state_abbr": "ND",
            }
        ],
    }
    agencies = parse_directory(payload, "ND")
    assert [a.ori for a in agencies] == ["ND0090200", "ND0270000"]
    assert agencies[0].type == "city" and agencies[0].latitude == 46.927
    assert agencies[1].counties == "McKenzie"
