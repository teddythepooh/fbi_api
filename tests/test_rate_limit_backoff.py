'''
If the rate limit is reached, this test verifies that _wait_for_rate_limit_reset() is triggered.
'''
from fbi_api import FBI

def test_wait_triggered_at_zero_rate_limit(fbi_client, mocker):
    mock_wait = mocker.patch.object(fbi_client, "_wait_for_rate_limit_reset")

    mock_response = mocker.MagicMock()
    mock_response.headers = {"X-Ratelimit-Remaining": "0"}
    mock_response.status_code = 200
    mocker.patch.object(fbi_client.session, "get", return_value = mock_response)

    url = f"{FBI.base_url}/agency/byStateAbbr/IL"
    fbi_client.get(url)  # this will set the rate limit to 0
    fbi_client.get(url)  # the second API call should trigger _wait_for_rate_limit_reset()

    mock_wait.assert_called()
