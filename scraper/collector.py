import requests
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .parser import (fetch_and_parse, parse_state_links,
                    parse_state_details, parse_election_results_table)
from models.data_models import StateData, YearData, ElectionResult, Party
from scraper.years import scrape_election_year 

class StateElectionScraper:
    """
    Orchestrates scraping state pages and national year pages,
    uses parser functions, and populates data model objects.
    Attempts to find all fields defined in models.
    """
    BASE_URL = "https://www.270towin.com"
    STATES_LIST_URL = f"{BASE_URL}/states/"
    DEFAULT_TARGET_YEARS = [2020, 2016, 2012, 2008, 2004, 2000, 1996, 1992]
    MAX_WORKERS = 5  

    def __init__(self, target_years: Optional[List[int]] = None, delay_seconds: float = 0.5):
        self.target_years = sorted(list(set(target_years))) if target_years else self.DEFAULT_TARGET_YEARS
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        self.national_year_data: Dict[int, Dict[str, Any]] = {}
        print(f"Initialized scraper for years: {self.target_years} with delay {self.delay_seconds}s.")

    def _fetch_national_year_data(self):
        """Fetches national leader and vote data for each target year."""
        print(f"\nFetching national data for years: {self.target_years}...")
        for year in self.target_years:
            print(f"  Fetching national data for {year}...")
            year_results = scrape_election_year(year) 
            if year_results:
                year_entry = {
                    'dem_leader': None, 
                    'rep_leader': None, 
                    'dem_votes': None, 
                    'rep_votes': None,
                    'winner_image_url': None
                }
                for candidate_data in year_results:
                    party = candidate_data.get("party")
                    leader = candidate_data.get("leader")
                    pop_votes = candidate_data.get("popular_votes")
                    winner_image_url = candidate_data.get("winner_image_url")
                    
                    if party == "Democratic":
                        year_entry['dem_leader'] = leader
                        year_entry['dem_votes'] = pop_votes 
                        if winner_image_url:
                            year_entry['winner_image_url'] = winner_image_url
                    elif party == "Republican":
                        year_entry['rep_leader'] = leader
                        year_entry['rep_votes'] = pop_votes 
                        if winner_image_url:
                            year_entry['winner_image_url'] = winner_image_url
                            
                self.national_year_data[year] = year_entry
                print(f"    -> Stored national data for {year}.")
            else:
                print(f"    -> Warning: Could not fetch or parse national data for {year}. Leader/Vote fields will be None.")
                self.national_year_data[year] = {} 

    def get_state_links_and_names(self) -> Dict[str, str]:
        """ Fetches and parses main states page for state names and URLs. """
        print(f"\nFetching state list from {self.STATES_LIST_URL}...")
        soup = fetch_and_parse(self.STATES_LIST_URL, self.session, self.delay_seconds)
        state_links = parse_state_links(soup) if soup else {}
        print(f"Found {len(state_links)} state links.")
        return state_links

    def scrape_single_state(self, state_name: str, state_url_path: str) -> List[ElectionResult]:
        """
        Scrapes data for one state, attempts to find all model fields,
        and returns a list of ElectionResult objects. Uses pre-fetched national data.
        """
        full_url = self.BASE_URL + state_url_path
        print(f"  Scraping {state_name} from {full_url}...")
        results_for_state: List[ElectionResult] = []

        soup = fetch_and_parse(full_url, self.session, self.delay_seconds)
        if not soup:
            print(f"  Could not fetch or parse page for {state_name}. Skipping.")
            return results_for_state

        state_details = parse_state_details(soup)
        electoral_votes = state_details.get('electoral_votes')
        total_population = state_details.get('total_population') 

        try:
            state_obj = StateData(
                state_name=state_name,
                electoral_votes=electoral_votes,
                total_population=total_population
            )
        except (ValueError, TypeError) as e:
            print(f"  Error creating StateData for {state_name}: {e}. Skipping state.")
            return results_for_state

        parsed_state_yearly_data = parse_election_results_table(soup, self.target_years)
        print(f"    Found {len(parsed_state_yearly_data)} yearly state results matching target years.")

        year_obj_cache: Dict[int, YearData] = {}

        for state_year_data in parsed_state_yearly_data:
            year = state_year_data.get('year')
            if year is None:
                continue

            national_data = self.national_year_data.get(year, {})

            try:
                if year not in year_obj_cache:
                    year_obj = YearData(
                        year=year,
                        dem_leader=national_data.get('dem_leader'),
                        rep_leader=national_data.get('rep_leader'),
                        dem_votes=national_data.get('dem_votes'),
                        rep_votes=national_data.get('rep_votes'),
                        total_votes=None,
                        winner_image_url=national_data.get('winner_image_url')
                    )
                    year_obj_cache[year] = year_obj
                else:
                    year_obj = year_obj_cache[year]

                result_obj = ElectionResult(
                    state_info=state_obj,
                    year_info=year_obj,
                    dem_percentage=state_year_data.get('dem_pct'),
                    rep_percentage=state_year_data.get('rep_pct'),
                    winner=state_year_data.get('winner') 
                )
                results_for_state.append(result_obj)
            except (ValueError, TypeError) as e:
                print(f"    Error creating model objects for {state_name} year {year}: {e}. Skipping year.")
                continue

        return results_for_state

    def scrape_all_states(self) -> List[ElectionResult]:
        """ Orchestrates scraping all states, returns list of ElectionResult objects. """
        self._fetch_national_year_data()

        all_election_results: List[ElectionResult] = []
        state_links = self.get_state_links_and_names()
        if not state_links:
            return all_election_results

        print(f"\nStarting state page scraping for {len(state_links)} states...")
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
                        print(f"  Finished {state_name}. Added {len(state_results)} results.")
                except Exception as e:
                    print(f"  Error processing {state_name}: {e}")

        print(f"\nScraping finished. Collected {len(all_election_results)} total election results.")
        return all_election_results