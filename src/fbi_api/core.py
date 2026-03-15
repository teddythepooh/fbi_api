import os
import requests
import pandas as pd
from pathlib import Path
from .utils import load_yaml

class FBI:
    base_url = "https://api.usa.gov/crime/fbi/cde"
    config = load_yaml(Path(__file__).parent.joinpath("config.yml"))
    
    def __init__(self, api_key: str = None):
        '''
        If no api_key is passed, it is invoked from environment variable "FBI_API_KEY."
        '''
        self.api_key = api_key

    @staticmethod
    def _get_state_abbrs() -> list:
        return FBI.config["state_abbrs"]
    
    @staticmethod
    def _get_offenses() -> dict:
        return FBI.config["offenses"]
        
    def _get_api_key(self) -> str:
        return os.getenv("FBI_API_KEY", default = self.api_key)
    
    def _add_key_to_call(self, api_call: str) -> str:
        prefix = "&" if "?" in api_call else "?"

        auth_str = f"{prefix}API_KEY={self._get_api_key()}"
        
        if not api_call.endswith(auth_str):
            api_call = f"{api_call}{auth_str}"
        
        return api_call
    
    def get(self, api_call: str, timeout_limit: int = 10) -> dict:
        api_call = self._add_key_to_call(api_call)
        response = requests.get(api_call, timeout = timeout_limit)
        
        return response.json() if response.status_code == 200 else None

    def _oris_by_state(self, state_abbr: str) -> pd.DataFrame:
        nested = self.get(f"{FBI.base_url}/agency/byStateAbbr/{state_abbr}")

        flattened = []

        for agencies in nested.values():
            for agency in agencies:
                flattened.append(agency)
        
        return pd.DataFrame(flattened)
    
    def get_metadata(self, state_abbr: str) -> pd.DataFrame:
        '''
        state_abbr: State abbreviation of desired state.
        
        Extracts the metadata for a state, namely all law enforcement agencies that have provided data to the 
        Uniform Crime Reporting (UCR) program. If metadata for all states are desired, set state_abbr to "all."
        '''
        if state_abbr == "all":
            results = []
            
            for state in FBI._get_state_abbrs():
                print(f"Extracting metadata for {state}...")
                results.append(self._oris_by_state(state))
                
            return pd.concat(results, ignore_index = True)
        else:
            return self._oris_by_state(state_abbr)
    
    def get_crime_statistics(self, ori: str, year: int, offense: str) -> pd.DataFrame:
        '''
        ori: The originating agency identifier (ORI). Invoke get_metadata() to extract all ORIs in a state.
        year: The year.
        
        Extracts the monthly crime statistics reported by an agency.
        '''
        try:
            offense_mapping = FBI._get_offenses()[offense]
            api_call = self.get(
                f"{FBI.base_url}/summarized/agency/{ori}/{offense_mapping}?from=01-{year}&to=12-{year}"
                )
        except KeyError:
            raise KeyError(f"Valid offenses to pass are {", ".join(list(FBI._get_offenses().keys()))}.")
    
        last_refresh_date = api_call["cde_properties"]["last_refresh_date"]["UCR"]
        
        _, first_value = next(iter(api_call["offenses"]["actuals"].items()))

        crime_statistics = pd.Series(first_value, name = "count").rename_axis("date").reset_index()
        
        month_year_columns = ["month", "year"]
        crime_statistics[month_year_columns] = crime_statistics["date"].str.split("-", expand = True)
        crime_statistics.drop(columns = "date", inplace = True)
        
        crime_statistics["ori"] = ori
        crime_statistics["offense"] = offense
        crime_statistics["last_refresh_date"] = last_refresh_date
        
        for col in month_year_columns:
            crime_statistics[col] = crime_statistics[col].astype(int)
            
        crime_statistics.sort_values(by = month_year_columns, inplace = True)
        
        return crime_statistics[["ori", "month", "year", "offense", "count", "last_refresh_date"]]
