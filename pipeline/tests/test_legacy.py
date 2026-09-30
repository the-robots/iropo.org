from iropo_pipeline import config
from iropo_pipeline.directory import DirectoryAgency
from iropo_pipeline.legacy import (
    LegacyAgency,
    crosswalk,
    is_valid_ori,
    lookalike_candidates,
    read_legacy_workbook,
)


def agency(ori, name, counties=None):
    return DirectoryAgency(
        ori=ori,
        name=name,
        type="city",
        state="NC",
        counties=counties,
        latitude=None,
        longitude=None,
        nibrs=True,
        nibrs_since=None,
    )


def legacy(ori, name, city=None, county=None, sheet="LAW ENFORCEMENT NORTH CAROLINA"):
    return LegacyAgency(state="NC", sheet=sheet, agency=name, city=city, county=county, ori=ori)


def test_ori_format():
    assert is_valid_ori("NC0630100")
    assert is_valid_ori("NY059070G")
    assert not is_valid_ori("NC063010")
    assert not is_valid_ori("nc0630100")


def test_lookalike_candidates_cover_common_ocr_confusions():
    assert "NC0060100" in lookalike_candidates("NC0060I00")
    assert "NC0180500" in lookalike_candidates("NC0180S00")
    assert "NC0070100" in lookalike_candidates("NC007010Q")
    assert "NC0060I00" not in lookalike_candidates("NC0060I00")


def test_crosswalk_statuses():
    directory = [
        agency("NC0630100", "Aberdeen Police Department", "Moore"),
        agency("NC0060100", "Newland Police Department", "Avery"),
        agency("NC0100100", "Oak Island Police Department", "Brunswick"),
    ]
    rows = crosswalk(
        [
            legacy("NC0630100", "ABERDEEN PD", "ABERDEEN", "MOORE"),
            legacy("NC0060I00", "NEWLAND PD", "NEWLAND", "AVERY"),
            legacy("NCDI00100", "CAPE HATTERAS NATIONAL SEASHORE", sheet="FEDERAL AGENCIES NC"),
            legacy("NCD100100", "SOME OTHER PD", "ELSEWHERE"),
            legacy("NC9999999", "DEFUNCT PD"),
        ],
        directory,
    )
    assert [r.status for r in rows] == [
        "current",
        "likely_ocr_error",
        "federal",
        "not_found",
        "not_found",
    ]
    assert rows[0].name_consistent is True
    assert rows[1].current.ori == "NC0060100"


def test_reads_repository_legacy_spreadsheets():
    path = config.LEGACY_DIR / "agency-directories" / "localAndStateAgencies-NC.xlsx"
    rows = read_legacy_workbook(path, "NC")
    assert len(rows) > 600
    assert rows[0].ori == "NC0630100" and rows[0].agency == "ABERDEEN PD"
    nd_rows = read_legacy_workbook(path.with_name("localAndStateAgencies-ND.xlsx"), "ND")
    assert nd_rows and all(r.sheet == "LAW ENFORCEMENT NORTH DAKOTA" for r in nd_rows)
