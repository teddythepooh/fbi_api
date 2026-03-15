'''
If the rate limit is reached, _wait_for_rate_limit_reset() should be triggered.
'''
from fbi_api import FBI

def test_wait_triggered_at_zero_rate_limit(fbi_client, mocker):
    mock_wait = mocker.patch.object(fbi_client, "_wait_for_rate_limit_reset")
    fbi_client.rate_limit = 0
    fbi_client.get(f"{FBI.base_url}/agency/byStateAbbr/IL") # the actual endpoint is irrelevent here
    
    mock_wait.assert_called()
