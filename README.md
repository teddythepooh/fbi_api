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

# See ./metadata_all.csv for expected result.
metadata = api.get_metadata(state_abbr = "all") 

# ORI stands for Originating Agency Identifer (ORI), uniquely identifying the law enforcement
# agencies that report to the FBI. All ORIs in a state can be found in api.get_metadata().
crime_statistics = api.get_crime_statistics(ori = "NY0303000", year = 2024, offense = "Violent Crimes")
```

Alternatively, to see what `get_crime_statistics()` looks like for NYC, go to GitHub Actions. Under `Actions` -> `NYC Crime Statistics`, click any successful workflow then export the `nyc` artifact. This should download `nyc.zip` in your device.
