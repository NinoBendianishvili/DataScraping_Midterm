# main.py
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

    if not all_results:
        print("No results were collected.")
        return

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
    print(f"- Check the '{OUTPUT_DIR}' directory for '{CSV_FILENAME}' and '{JSON_FILENAME}' output files.")
    print("- Run 'analyzer.py' to generate visual reports from the collected data.")