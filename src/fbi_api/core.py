import os
import time
import requests
import warnings
import pandas as pd
import itertools
from tqdm import tqdm
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .utils import load_yaml

class FBI:
    '''
    Law enforcement agencies are uniquely identified by the originating agency identifier (ORI); get_metadata() 
    returns all ORIs by state. The state abbreviations that can be passed to get_metadata() can be found in 
    FBI.get_state_abbrs(). To retrieve metadata for all states, simply pass "all" to get_metadata(). Lastly, 
    the offenses supported in get_crime_statistics()'s offenses parameter can be found in FBI.get_offenses().
    '''
    base_url = "https://api.usa.gov/crime/fbi/cde"
    config = load_yaml(Path(__file__).parent.joinpath("config.yml"))
    
    status_code_forcelist = [502, 503, 504]
    
    def __init__(self, 
                 api_key: str = None,
                 timeout_limit: int = 15,
                 exponential_delay_factor: int = 2,
                 max_retries: int = 5):
        '''
        api_key (optional): If no api_key is passed, it is invoked from environment variable "FBI_API_KEY."
        timeout_limit (optional): Number of seconds to wait for a response before timing out. Defaults at 15.
        exponential_delay_factor (optional): Factor by which to increase delay between retries. Defaults at 2.
        max_retries (optional): Number of times to retry a request. Defaults at 5.
        '''
        self.api_key = api_key
        self.timeout_limit = timeout_limit
        self.max_retries = max_retries
        self.exponential_delay_factor = exponential_delay_factor

        self.session = self._build_session()
        self.rate_limit = None

        self._validate_api_config()

    def _validate_api_config(self) -> None:
        '''
        Validates configuration parameters.
        '''
        if not self.timeout_limit > 0 or not self.max_retries > 0:
            raise ValueError("timeout_limit and max_retries should be greater than 0.")
        
        if self.exponential_delay_factor == 0:
            warnings.warn("No delay between retries because exponential_delay_factor is 0.")

    def _build_session(self) -> requests.Session:
        '''
        Instantiates requests session. The API call is retried up to self.max_retries times if status code is in 
        FBI.status_code_forcelist. The delay between retries is exponential by a factor of exponential_delay_factor.
        '''
        session = requests.Session()
        retry = Retry(
            total = self.max_retries,
            backoff_factor = self.exponential_delay_factor,
            status_forcelist = FBI.status_code_forcelist
        )
        session.mount("https://", HTTPAdapter(max_retries = retry))
        
        return session

    @staticmethod
    def get_state_abbrs() -> list:
        return FBI.config["state_abbrs"]
    
    @staticmethod
    def get_offenses() -> dict:
        return FBI.config["offenses"]
    
    @staticmethod
    def _agency_metrics_column_mapping() -> dict:
        return {
            "Male Officers": "num_male_officers",
            "Female Officers": "num_female_officers",
            "Male Civilians": "num_male_civilians",
            "Female Civilians": "num_female_civilians",
        }

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
            
            for state in tqdm(FBI.get_state_abbrs(), desc = "Extracting metadata for all states"):
                results.append(self._oris_by_state(state))
            
            print("Success!")
                
            return pd.concat(results, ignore_index = True)
        else:
            return self._oris_by_state(state_abbr)
    
    def _get_crime_statistics(self, ori: str, year: int, offense: str) -> pd.DataFrame:
        try:
            offense_mapping = FBI.get_offenses()[offense]
            api_call = self.get(f"{FBI.base_url}/summarized/agency/{ori}/{offense_mapping}?from=01-{year}&to=12-{year}")
        except KeyError:
            raise KeyError(f"Valid offenses to pass are {', '.join(list(FBI.get_offenses().keys()))}.")

        _, first_value = next(iter(api_call["offenses"]["actuals"].items()))

        crime_statistics = (
            pd.Series(first_value, name = "count")
            .rename_axis("date")
            .reset_index()
            .assign(
                ori = ori,
                month = lambda df: df["date"].str.split("-").str[0].astype(int),
                year = lambda df: df["date"].str.split("-").str[1].astype(int),
                offense = offense,
                last_refresh_date = api_call["cde_properties"]["last_refresh_date"]["UCR"],
            )
        )
        
        return crime_statistics
        
    def _get_agency_metrics(self, ori: str, year: int) -> pd.DataFrame:
        api_call = self.get(f"{FBI.base_url}/pe/{ori[:2]}/{ori}?from={year}&to={year}")
        
        agency_metrics = (
            pd.DataFrame(api_call["actuals"])
            .rename_axis("year")
            .reset_index()
            .assign(
                ori = ori,
                year = year,
                population = api_call["populations"]["Participated Population"][str(year)],
                last_refresh_date = api_call["cde_properties"]["last_refresh_date"]["UCR"]
                )
            .rename(columns = FBI._agency_metrics_column_mapping())
            )
        
        return agency_metrics
    
    def get_crime_statistics(self, 
                             ori: str | list, 
                             year: int | list, 
                             offense: str | list,
                             flag_anomalies_with_ai: bool = False) -> pd.DataFrame:
        '''
        ori: Originating agency identifier (ORI) or list of ORIs. To see all valid ORIs, do get_metadata("all").
        year: The year or list of years.
        offense: Offense or list of offenses. To see all valid offenses, do FBI.get_offenses().
        flag_anomalies_with_ai: Whether to run AI-powered anomaly detection to flag suspicious counts.

        Extracts monthly crime statistics reported by the police agency.
        '''
        combinations = list(itertools.product(
            ori if isinstance(ori, list) else [ori], 
            year if isinstance(year, list) else [year],
            offense if isinstance(offense, list) else [offense]
            )
        )

        print(f"Executing {len(combinations)} quer{'y' if len(combinations) == 1 else 'ies'}...")
        results = []

        for o, y, off in tqdm(combinations):
            results.append(self._get_crime_statistics(ori = o, year = y, offense = off))
        
        results_out = pd.concat(results, ignore_index = True)[
            ["ori", 
             "month", 
             "year", 
             "offense", 
             "count", 
             "last_refresh_date"]
            ]
        
        if flag_anomalies_with_ai:
            from .ai import AnomalyDetection
            AnomalyDetection().flag_anomalies_with_ai(results_out)

        return results_out
    
    def get_agency_metrics(self, 
                           ori: str | list, 
                           year: int | list) -> pd.DataFrame:
        '''
        ori: Originating agency identifier (ORI) or list of ORIs. To see all valid ORIs, do get_metadata("all").
        year: The year or list of years.
        
        Extracts the number of sworn and non-sworn officers in the police agency (and the total population they serve).
        '''
        combinations = list(itertools.product(
            ori if isinstance(ori, list) else [ori], 
            year if isinstance(year, list) else [year],
            )
        )

        print(f"Executing {len(combinations)} quer{'y' if len(combinations) == 1 else 'ies'}...")
        results = []
        
        for o, y in tqdm(combinations):
            results.append(self._get_agency_metrics(ori = o, year = y))

        return pd.concat(results, ignore_index = True)[
            ["ori", 
            "year", 
            "population",
            *FBI._agency_metrics_column_mapping().values(),
            "last_refresh_date"]
            ]
