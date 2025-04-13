# main.py
# ... (keep existing imports)
from models.data_models import Party

def run_test_scrape():
    # ... (previous code until results display)

        # Access the new fields
        dem_votes = result.year_info.dem_votes
        rep_votes = result.year_info.rep_votes
        winner = result.winner.value if result.winner else 'N/A'

        print(f"Result #{count + 1}:")
        print(f"  State Info:")
        print(f"    Name: {state_name}")
        print(f"    EV:   {state_ev if state_ev is not None else 'N/A'}")
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