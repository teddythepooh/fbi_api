import os
import requests
import pandas as pd
from pathlib import Path
from .utils import load_yaml

class FBIAPI:
    base_url = "https://api.usa.gov/crime/fbi/cde"
    config = load_yaml(Path(__file__).parent.joinpath("config.yml"))
    
    def __init__(self, api_key: str = None):
        '''
        If no api_key is passed, it is invoked from the environment variable "FBI_API_KEY."
        '''
        self.api_key = api_key
        
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
        
        return response.json()
    
    def _get_state_abbrs() -> list:
        return FBIAPI.config["state_abbrs"]

    def _oris_by_state(self, state_abbr: str) -> pd.DataFrame:
        nested = self.get(f"{self.base_url}/agency/byStateAbbr/{state_abbr}")

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
            
            for state in self._get_state_abbrs():
                print(f"Extracting metadata for {state}...")
                results.append(self._oris_by_state(state))
                
            return pd.concat(results, ignore_index=True)
        else:
            return self._oris_by_state(state_abbr)
