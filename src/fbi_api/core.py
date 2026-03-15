import os
import time
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .utils import load_yaml

class FBI:
    base_url = "https://api.usa.gov/crime/fbi/cde"
    config = load_yaml(Path(__file__).parent.joinpath("config.yml"))
    
    def __init__(self, 
                 api_key: str = None,
                 timeout_limit: int = 15,
                 max_retries: int = 5,
                 exponential_delay_factor: int = 2):
        '''
        api_key (optional): If no api_key is passed, it is invoked from environment variable "FBI_API_KEY."
        timeout_limit (optional): Number of seconds to wait for a response before timing out. Defaults at 15.
        max_retries (optional): Number of times to retry a request. Defaults at 5.
        exponential_delay_factor (optional): Factor by which to increase delay between retries. Defaults at 2.
        '''
        self.api_key = api_key
        self.timeout_limit = timeout_limit
        self.max_retries = max_retries
        self.exponential_delay_factor = exponential_delay_factor

        self.session = self._build_session()
        self.rate_limit = None
        
    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total = self.max_retries,
            backoff_factor = self.exponential_delay_factor,
            status_forcelist = [502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries = retry))
        
        return session

    @staticmethod
    def get_state_abbrs() -> list:
        return FBI.config["state_abbrs"]
    
    @staticmethod
    def get_offenses() -> dict:
        return FBI.config["offenses"]
        
    def _get_api_key(self) -> str:
        return os.getenv("FBI_API_KEY", default = self.api_key)
    
    def _add_key_to_call(self, api_call: str) -> str:
        prefix = "&" if "?" in api_call else "?"

        auth_str = f"{prefix}API_KEY={self._get_api_key()}"
        
        if not api_call.endswith(auth_str):
            api_call = f"{api_call}{auth_str}"
        
        return api_call
    
    def _wait_for_rate_limit_reset(self, wait_time: int = 3600) -> None:
        for _ in tqdm(range(wait_time), desc = "Rate limit reached. Resuming in", unit = "s"):
            time.sleep(1)
    
    def get(self, api_call: str) -> dict:
        if self.rate_limit == 0:
            self._wait_for_rate_limit_reset()

        api_call = self._add_key_to_call(api_call)
        response = self.session.get(api_call, timeout = self.timeout_limit)

        self.rate_limit = int(response.headers["X-Ratelimit-Remaining"])

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
        state_abbr: To see all valid state abbreviations, do FBI.get_state_abbrs(). If metadata for 
        all states are desired, set this to "all."
        
        Returns all law enforcement agencies in a state that have provided data to the Uniform Crime 
        Reporting (UCR) program.
        '''
        if state_abbr == "all":
            results = []
            
            for state in FBI.get_state_abbrs():
                print(f"Extracting metadata for {state}...")
                results.append(self._oris_by_state(state))
                
            return pd.concat(results, ignore_index = True)
        else:
            return self._oris_by_state(state_abbr)
    
    def get_crime_statistics(self, ori: str, year: int, offense: str) -> pd.DataFrame:
        '''
        ori: Originating agency identifier (ORI). To see all valid ORIs, do get_metadata('all').
        year: The year.
        offense: To see all valid offenses, do FBI.get_offenses().
        
        Extracts the monthly crime statistics reported by an agency.
        '''
        try:
            offense_mapping = FBI.get_offenses()[offense]
            api_call = self.get(
                f"{FBI.base_url}/summarized/agency/{ori}/{offense_mapping}?from=01-{year}&to=12-{year}"
                )
        except KeyError:
            raise KeyError(f"Valid offenses to pass are {", ".join(list(FBI.get_offenses().keys()))}.")
    
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
