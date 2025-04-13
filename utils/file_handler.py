# utils/file_handler.py
import csv
import json
import os
from typing import List, Dict, Any
from models.data_models import ElectionResult

def _create_output_dir(dir_path: str = "output"):
    """Creates the output directory if it doesn't exist."""
    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}")
        raise 

def save_to_csv(results: List[ElectionResult], filename: str = "election_results.csv", output_dir: str = "output"):
    """
    Saves the list of ElectionResult objects to a CSV file.
    Data includes state info, national year info (leaders/votes), and state percentages/winner.
    """
    if not results:
        print("No results to save to CSV.")
        return

    _create_output_dir(output_dir)
    filepath = os.path.join(output_dir, filename)
    print(f"Saving data to CSV: {filepath}...")

    header = [
        'state_name', 'electoral_votes', 'total_population', 
        'year', 'dem_leader', 'rep_leader', 'dem_national_votes', 'rep_national_votes', 'total_national_votes',
        'dem_state_percentage', 'rep_state_percentage', 'state_winner', 'winner_image_url'
    ]

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header) 

            for result in results:
                state_info = result.state_info
                year_info = result.year_info

                row = [
                    state_info.state_name,
                    state_info.electoral_votes if state_info.electoral_votes is not None else '',
                    state_info.total_population if state_info.total_population is not None else '', 
                    year_info.year,
                    year_info.dem_leader if year_info.dem_leader else '',
                    year_info.rep_leader if year_info.rep_leader else '',
                    year_info.dem_votes if year_info.dem_votes is not None else '',
                    year_info.rep_votes if year_info.rep_votes is not None else '', 
                    year_info.total_votes if year_info.total_votes is not None else '', 
                    result.dem_percentage if result.dem_percentage is not None else '', 
                    result.rep_percentage if result.rep_percentage is not None else '',
                    result.winner.value if result.winner else '',
                    year_info.winner_image_url if year_info.winner_image_url else ''
                ]
                writer.writerow(row)
        print(f"Successfully saved {len(results)} results to {filepath}")
    except IOError as e:
        print(f"Error writing to CSV file {filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV saving: {e}", exc_info=True)


def _convert_result_to_dict(result: ElectionResult) -> Dict[str, Any]:
    """Converts an ElectionResult object to a dictionary suitable for JSON."""
    return {
        "state_info": {
            "state_name": result.state_info.state_name,
            "electoral_votes": result.state_info.electoral_votes,
            "total_population": result.state_info.total_population 
        },
        "year_info": {
            "year": result.year_info.year,
            "dem_leader": result.year_info.dem_leader,
            "rep_leader": result.year_info.rep_leader,
            "dem_national_votes": result.year_info.dem_votes,
            "rep_national_votes": result.year_info.rep_votes,
            "total_national_votes": result.year_info.total_votes,
            "winner_image_url": result.year_info.winner_image_url
        },
        "state_election_details": {
            "dem_state_percentage": result.dem_percentage,
            "rep_state_percentage": result.rep_percentage,
            "state_winner": result.winner.value if result.winner else None 
        }
    }

def save_to_json(results: List[ElectionResult], filename: str = "election_results.json", output_dir: str = "output"):
    """
    Saves the list of ElectionResult objects to a JSON file with nested structure.
    """
    if not results:
        print("No results to save to JSON.")
        return

    _create_output_dir(output_dir)
    filepath = os.path.join(output_dir, filename)
    print(f"Saving data to JSON: {filepath}...")

    data_to_save = [_convert_result_to_dict(result) for result in results]

    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(results)} results to {filepath}")
    except IOError as e:
        print(f"Error writing to JSON file {filepath}: {e}")
    except TypeError as e:
         print(f"Error serializing data to JSON: {e}") 
    except Exception as e:
        print(f"An unexpected error occurred during JSON saving: {e}", exc_info=True)