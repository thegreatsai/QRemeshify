import openpyxl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.importer.xlsm_importer import import_reference_lists, import_site
from app.models.reference_data import ReferenceList


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()


def _write_fixture(path, school_info_values=None):
    wb = openpyxl.Workbook()
    data_lists = wb.active
    data_lists.title = "Data Lists"
    data_lists.append(["Cable Type", "Room Type"])
    data_lists.append(["CAT5E", "MDF"])
    data_lists.append(["CAT6", "IDF"])
    data_lists.append(["", "Classroom"])

    school_info = wb.create_sheet("School Information")
    school_info["A4"] = "Building Code"
    school_info["A5"] = "Rack ID"
    if school_info_values:
        school_info["F4"] = school_info_values.get("building_code")
        school_info["F5"] = school_info_values.get("rack_id")

    wb.save(path)


def test_import_reference_lists(tmp_path, db_session):
    fixture = tmp_path / "site.xlsm"
    _write_fixture(fixture)

    counts = import_reference_lists(fixture, db_session)
    assert counts == {"cable_type": 2, "room_type": 3}

    cable_type = db_session.query(ReferenceList).filter_by(key="cable_type").first()
    assert {item.value for item in cable_type.items} == {"CAT5E", "CAT6"}


def test_import_reference_lists_is_idempotent(tmp_path, db_session):
    fixture = tmp_path / "site.xlsm"
    _write_fixture(fixture)

    import_reference_lists(fixture, db_session)
    counts = import_reference_lists(fixture, db_session)
    assert counts == {"cable_type": 0, "room_type": 0}


def test_import_site_rejects_blank_template(tmp_path, db_session):
    fixture = tmp_path / "blank.xlsm"
    _write_fixture(fixture)

    with pytest.raises(ValueError, match="blank template"):
        import_site(fixture, db_session, name="Should Fail")


def test_import_site_success(tmp_path, db_session):
    fixture = tmp_path / "filled.xlsm"
    _write_fixture(fixture, school_info_values={"building_code": "27Q273", "rack_id": "MDF-1"})

    site = import_site(fixture, db_session, name="PS 273", district="27")
    assert site.building_code == "27Q273"
    assert site.rack_id == "MDF-1"
    assert site.name == "PS 273"
