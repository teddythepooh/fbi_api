import pytest
from fbi_api import FBIAPI
 
EXPECTED_COLUMNS = {
    "ori",
    "counties",
    "is_nibrs",
    "latitude",
    "longitude",
    "state_abbr",
    "state_name",
    "agency_name",
    "agency_type_name",
    "nibrs_start_date"
}

@pytest.fixture(scope = "module")
def illinois_metadata():
    api = FBIAPI()
    return api.get_metadata("IL")

def test_expected_columns(illinois_metadata):
    assert set(illinois_metadata.columns) == EXPECTED_COLUMNS
 
def test_non_zero_rows(illinois_metadata):
    assert len(illinois_metadata) > 0
