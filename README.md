# FBI Crime Data API
This is a wrapper around the FBI Crime Data API, the first of its kind as of March 2026.

## Example
After signing up for an API key in https://api.data.gov/signup/, 

```bash
pip install fbi-data-api
```

```python
from fbi_api import FBI

# If no api_key is passed, your environment variable FBI_API_KEY is automatically invoked.
api = FBI(api_key = your_api_key)

metadata = api.get_metadata(state_abbr = "all")

# ORI stands for Originating Agency Identifer (ORI), uniquely identifying the law enforcement
# agencies that report to the FBI. The ORIs in a state can be extracted from api.get_metadata().
crime_statistics = api.get_crime_statistics(ori = "ILCPD0000", year = 2024, offense = "Violent Crimes")
```
