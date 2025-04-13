# scraper/collector.py
# ... (keep existing imports)
from models.data_models import Party

class StateElectionScraper:
    # ... (keep existing methods)

    def scrape_single_state(self, state_name: str, state_url_path: str) -> List[ElectionResult]:
        # ... (previous code until year_data_dict loop)

        for year_data_dict in parsed_yearly_data:
            year = year_data_dict.get('year')
            if year is None: continue

            # Get all available data
            dem_leader = year_data_dict.get('dem_leader')
            rep_leader = year_data_dict.get('rep_leader')
            dem_pct = year_data_dict.get('dem_pct')
            rep_pct = year_data_dict.get('rep_pct')
            dem_votes = year_data_dict.get('dem_votes')
            rep_votes = year_data_dict.get('rep_votes')
            total_votes = year_data_dict.get('total_votes')
            winner = year_data_dict.get('winner')

            try:
                year_obj = YearData(
                    year=year,
                    dem_leader=dem_leader,
                    rep_leader=rep_leader,
                    dem_votes=dem_votes,
                    rep_votes=rep_votes,
                    total_votes=total_votes
                )

                result_obj = ElectionResult(
                    state_info=state_obj,
                    year_info=year_obj,
                    dem_percentage=dem_pct,
                    rep_percentage=rep_pct,
                    winner=winner
                )
                results_for_state.append(result_obj)
            except (ValueError, TypeError) as e:
                print(f"    Error creating model objects for {state_name} year {year}: {e}. Skipping year.")
                continue

        return results_for_state