# main.py
import time
from typing import List
from scraper.collector import StateElectionScraper
from models.data_models import Party, ElectionResult, StateData, YearData

# --- Configuration ---
TARGET_YEARS = [2020, 2016, 2012]  # Example target years
SCRAPER_DELAY_SECONDS = 1.0

def run_test_scrape():
    """Runs the scraper and prints test output for all model fields."""
    print("-" * 30)
    print("Starting Scraper Test...")
    print("-" * 30)

    scraper = StateElectionScraper(
        target_years=TARGET_YEARS,
        delay_seconds=SCRAPER_DELAY_SECONDS
    )

    # Run the full scrape process -> returns List[ElectionResult]
    all_results: List[ElectionResult] = scraper.scrape_all_states()

    # --- Comprehensive Test Output ---
    print("\n" + "-" * 30)
    print("Test Output: Displaying all fields for first few results...")
    print("-" * 30)

    if not all_results:
        print("No results were collected.")
        return

    results_to_show = 5  # Show fewer results to keep output manageable
    count = 0
    for result in all_results:
        if count >= results_to_show:
            break

        # Access data via the nested objects
        state_name = result.state_info.state_name
        state_ev = result.state_info.electoral_votes
        state_pop = result.state_info.total_population

        year = result.year_info.year
        dem_leader = result.year_info.dem_leader
        rep_leader = result.year_info.rep_leader
        dem_votes = result.year_info.dem_votes
        rep_votes = result.year_info.rep_votes
        total_votes = result.year_info.total_votes

        dem_pct = result.dem_percentage
        rep_pct = result.rep_percentage
        winner = result.winner.value if result.winner else 'N/A'

        print(f"Result #{count + 1}:")
        print(f"  State Info:")
        print(f"    Name: {state_name}")
        print(f"    EV:   {state_ev if state_ev is not None else 'N/A'}")
        print(f"    Pop:  {state_pop if state_pop is not None else 'N/A'}")
        print(f"  Year Info:")
        print(f"    Year: {year}")
        print(f"    DEM Leader: {dem_leader if dem_leader else 'N/A'}")
        print(f"    REP Leader: {rep_leader if rep_leader else 'N/A'}")
        print(f"    DEM Votes: {dem_votes if dem_votes is not None else 'N/A'}")
        print(f"    REP Votes: {rep_votes if rep_votes is not None else 'N/A'}")
        print(f"    Total Votes: {total_votes if total_votes is not None else 'N/A'}")
        print(f"  Percentages:")
        print(f"    DEM %: {dem_pct if dem_pct is not None else 'N/A'}")
        print(f"    REP %: {rep_pct if rep_pct is not None else 'N/A'}")
        print(f"  Winner: {winner}")
        print("-" * 20)

        count += 1

    if len(all_results) > results_to_show:
        print(f"... and {len(all_results) - results_to_show} more results collected.")

# --- Main Execution ---
if __name__ == "__main__":
    start_time = time.time()
    run_test_scrape()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("Note: Fields like Population, Leaders, Total Votes are likely 'N/A' as they aren't readily available on the scraped pages.")