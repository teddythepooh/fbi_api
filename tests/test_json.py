'''
The underlying API calls in get_metadata() and get_crime_statistics() return nested JSON objects. The tests below verify 
that they are correctly parsed to a tabular format.
'''
import json
from pathlib import Path

def load_mock_json(file: str):
    try:
        with open(Path(__file__).parent.joinpath("data").joinpath(file), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"{file} not found.")

MOCK_RESPONSE_GET_METADATA = load_mock_json("mock_response_get_metadata.json")
MOCK_RESPONSE_GET_CRIME_STATISTICS = load_mock_json("mock_response_get_crime_statistics.json")

def test_get_metadata(fbi_client, mocker):
    mocker.patch.object(fbi_client, "get", return_value = MOCK_RESPONSE_GET_METADATA)

    metadata = fbi_client.get_metadata("IL")

    assert set(metadata.columns) == {
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
    
    assert len(metadata) > 0

def test_get_crime_statistics(fbi_client, mocker):
    mocker.patch.object(fbi_client, "get", return_value = MOCK_RESPONSE_GET_CRIME_STATISTICS)

    crime_statistics = fbi_client.get_crime_statistics(ori = "ILCPD0000", year = 2024, offense = "Violent Crimes")

    assert set(crime_statistics.columns) == {
        "ori",
        "month",
        "year",
        "offense",
        "count",
        "last_refresh_date"
        }
    
    assert len(crime_statistics) > 0
