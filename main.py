import time
import os
from typing import List
from scraper.collector import StateElectionScraper
from models.data_models import Party, ElectionResult, StateData, YearData
from utils.file_handler import save_to_csv, save_to_json 

TARGET_YEARS = [2020, 2016, 2012, 2008, 2004, 2000]
SCRAPER_DELAY_SECONDS = 0.7 
OUTPUT_DIR = "output" 
CSV_FILENAME = "election_results_combined.csv" 
JSON_FILENAME = "election_results_combined.json"

def run_test_scrape():
    """Runs the scraper, prints test output, and saves results to files."""
    print("-" * 30)
    print("Starting Combined Scraper Run...")
    print("-" * 30)

    scraper = StateElectionScraper(
        target_years=TARGET_YEARS,
        delay_seconds=SCRAPER_DELAY_SECONDS
    )

    all_results: List[ElectionResult] = scraper.scrape_all_states()

    print("\n" + "-" * 30)
    print("Test Output: Displaying all fields for first few results...")
    print("-" * 30)

    if not all_results:
        print("No results were collected.")
        return

    results_to_show = 2 
    count = 0
    for result in all_results:
        if count >= results_to_show:
            break

        state_info = result.state_info
        year_info = result.year_info

        print(f"Result #{count + 1} ({state_info.state_name} - {year_info.year}):")
        print(f"  State Info:")
        print(f"    Name: {state_info.state_name}")
        print(f"    EV:   {state_info.electoral_votes if state_info.electoral_votes is not None else 'N/A'}")
        print(f"    Pop:  {state_info.total_population if state_info.total_population is not None else 'N/A'} (Expected N/A)") # Population not scraped
        print(f"  Year Info (National):")
        print(f"    Year: {year_info.year}")
        print(f"    DEM Leader: {year_info.dem_leader if year_info.dem_leader else 'N/A'}")
        print(f"    REP Leader: {year_info.rep_leader if year_info.rep_leader else 'N/A'}")
        print(f"    DEM Nat Votes: {year_info.dem_votes if year_info.dem_votes is not None else 'N/A'}")
        print(f"    REP Nat Votes: {year_info.rep_votes if year_info.rep_votes is not None else 'N/A'}")
        print(f"    Total Nat Votes: {year_info.total_votes if year_info.total_votes is not None else 'N/A'} (Expected N/A)") # Total Nat votes not directly scraped
        print(f"  State Election Details:")
        print(f"    DEM State %: {result.dem_percentage if result.dem_percentage is not None else 'N/A'}")
        print(f"    REP State %: {result.rep_percentage if result.rep_percentage is not None else 'N/A'}")
        print(f"    State Winner: {result.winner.value if result.winner else 'N/A'}")
        print("-" * 20)

        count += 1

    if len(all_results) > results_to_show:
        print(f"... and {len(all_results) - results_to_show} more results collected.")

    print("\n" + "-" * 30)
    print("Saving Results...")
    print("-" * 30)
    if all_results:
        save_to_csv(all_results, CSV_FILENAME, OUTPUT_DIR)
        save_to_json(all_results, JSON_FILENAME, OUTPUT_DIR)
    else:
        print("Skipping file saving as no results were collected.")

if __name__ == "__main__":
    start_time = time.time()
    run_test_scrape()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("\nNote:")
    print("- National leader names and popular votes should now be populated for most target years.")
    print("- State population and total national votes are generally 'N/A' as they aren't available/scraped.")
    print("- State-level percentages and winners are parsed from individual state pages.")
    print(f"- Check the '{OUTPUT_DIR}' directory for '{CSV_FILENAME}' and '{JSON_FILENAME}' output files.")