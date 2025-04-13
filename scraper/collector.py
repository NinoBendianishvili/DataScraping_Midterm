# scraper/collector.py
import requests
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .parser import (fetch_and_parse, parse_state_links,
                    parse_state_details, parse_election_results_table)
from models.data_models import StateData, YearData, ElectionResult, Party

class StateElectionScraper:
    """
    Orchestrates scraping, uses parser functions, and populates data model objects.
    Attempts to find all fields defined in models.
    """
    BASE_URL = "https://www.270towin.com"
    STATES_LIST_URL = f"{BASE_URL}/states/"
    DEFAULT_TARGET_YEARS = [2020, 2016, 2012, 2008, 2004, 2000, 1996, 1992]
    MAX_WORKERS = 5  # Number of concurrent requests

    def __init__(self, target_years: Optional[List[int]] = None, delay_seconds: float = 0.5):  # Reduced delay
        self.target_years = target_years if target_years else self.DEFAULT_TARGET_YEARS
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        print(f"Initialized scraper for years: {self.target_years} with delay {self.delay_seconds}s.")

    def get_state_links_and_names(self) -> Dict[str, str]:
        """ Fetches and parses main states page for state names and URLs. """
        print(f"Fetching state list from {self.STATES_LIST_URL}...")
        soup = fetch_and_parse(self.STATES_LIST_URL, self.session, self.delay_seconds)
        state_links = parse_state_links(soup) if soup else {}
        print(f"Found {len(state_links)} state links.")
        return state_links

    def scrape_single_state(self, state_name: str, state_url_path: str) -> List[ElectionResult]:
        """
        Scrapes data for one state, attempts to find all model fields,
        and returns a list of ElectionResult objects.
        """
        full_url = self.BASE_URL + state_url_path
        print(f"  Scraping {state_name} from {full_url}...")
        results_for_state: List[ElectionResult] = []

        soup = fetch_and_parse(full_url, self.session, self.delay_seconds)
        if not soup:
            print(f"  Could not fetch or parse page for {state_name}. Skipping.")
            return results_for_state

        # 1. Parse state-level info (EVs, Population attempt)
        state_details = parse_state_details(soup)
        electoral_votes = state_details.get('electoral_votes')
        total_population = state_details.get('total_population') # Will be None

        # 2. Create the StateData object
        try:
            state_obj = StateData(
                state_name=state_name,
                electoral_votes=state_details.get('electoral_votes'),
                total_population=state_details.get('total_population')
            )
        except (ValueError, TypeError) as e:
            print(f"  Error creating StateData for {state_name}: {e}. Skipping state.")
            return results_for_state

        # 3. Parse yearly results (Year, Leaders attempt, Pcts, Total Votes attempt)
        parsed_yearly_data = parse_election_results_table(soup, self.target_years)
        print(f"    Found {len(parsed_yearly_data)} yearly results matching target years.")

        # 4. Create YearData and ElectionResult objects
        year_obj_cache: Dict[int, YearData] = {} # Cache YearData objects if needed

        for year_data_dict in parsed_yearly_data:
            year = year_data_dict.get('year')
            if year is None:
                continue

            try:
                year_obj = YearData(
                    year=year,
                    dem_leader=year_data_dict.get('dem_leader'),
                    rep_leader=year_data_dict.get('rep_leader'),
                    dem_votes=year_data_dict.get('dem_votes'),
                    rep_votes=year_data_dict.get('rep_votes'),
                    total_votes=year_data_dict.get('total_votes')
                )

                result_obj = ElectionResult(
                    state_info=state_obj,
                    year_info=year_obj,
                    dem_percentage=year_data_dict.get('dem_pct'),
                    rep_percentage=year_data_dict.get('rep_pct'),
                    winner=year_data_dict.get('winner')
                )
                results_for_state.append(result_obj)
            except (ValueError, TypeError) as e:
                print(f"    Error creating model objects for {state_name} year {year}: {e}. Skipping year.")
                continue

        return results_for_state

    def scrape_all_states(self) -> List[ElectionResult]:
        """ Orchestrates scraping all states, returns list of ElectionResult objects. """
        all_election_results: List[ElectionResult] = []
        state_links = self.get_state_links_and_names()
        if not state_links:
            return all_election_results

        print(f"\nStarting scrape for {len(state_links)} states...")
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.scrape_single_state, state_name, state_url_path): state_name
                for state_name, state_url_path in state_links.items()
            }
            
            for future in as_completed(futures):
                state_name = futures[future]
                try:
                    state_results = future.result()
                    if state_results:
                        all_election_results.extend(state_results)
                        print(f"  Added {len(state_results)} results for {state_name}.")
                except Exception as e:
                    print(f"  Error processing {state_name}: {e}")

        print(f"\nScraping finished. Collected {len(all_election_results)} total election results.")
        return all_election_results