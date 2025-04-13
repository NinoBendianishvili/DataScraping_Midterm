# scraper/parser.py
# ... (keep existing imports)
from models.data_models import Party

def parse_election_results_table(soup: BeautifulSoup, target_years: List[int]) -> List[Dict[str, Any]]:
    """
    Parses the historical results table on a state page.
    Returns:
        List of dicts: [{'year': Y, 'dem_leader': L, 'rep_leader': L, 
                        'dem_pct': X, 'rep_pct': Y, 'dem_votes': V, 
                        'rep_votes': W, 'winner': Party}]
    """
    parsed_results = []
    if not soup: return parsed_results

    results_table = soup.find('table', id='recent_elections')
    if not results_table:
        print("Warning: Results table ('recent_elections') not found.")
        return parsed_results

    rows = results_table.select('tbody tr.toggle-row, tr.toggle-row')

    for row in rows:
        if row.get('style') and 'display:none' in row.get('style', ''): continue

        cells = row.find_all('td', recursive=False)
        if len(cells) < 2: continue

        year, dem_pct, rep_pct = None, None, None
        dem_votes, rep_votes, total_votes = None, None, None
        winner = None

        # Extract Year
        try:
            year_text = cells[0].get_text(strip=True)
            year_match = re.match(r'(\d{4})', year_text)
            if year_match: year = int(year_match.group(1))
        except Exception as e:
            print(f"Warning: Could not parse year: {e}")
            continue
        if year is None or year not in target_years: continue

        # Extract Percentages and determine winner
        try:
            nested_table = cells[1].find('table')
            if nested_table:
                nested_row = nested_table.find('tr')
                if nested_row:
                    nested_cells = nested_row.find_all('td')
                    if len(nested_cells) >= 1: 
                        dem_pct = parse_percentage(nested_cells[0].get_text(strip=True))
                    if len(nested_cells) >= 3: 
                        rep_pct = parse_percentage(nested_cells[2].get_text(strip=True))
                    
                    # Determine winner based on percentages
                    if dem_pct is not None and rep_pct is not None:
                        if dem_pct > rep_pct:
                            winner = Party.DEMOCRATIC
                        elif rep_pct > dem_pct:
                            winner = Party.REPUBLICAN
                        else:
                            winner = Party.OTHER
        except Exception as e:
             print(f"Warning (Year {year}): Error parsing percentages: {e}")

        parsed_results.append({
            'year': year,
            'dem_leader': None,  # Still not available
            'rep_leader': None,  # Still not available
            'dem_pct': dem_pct,
            'rep_pct': rep_pct,
            'dem_votes': dem_votes,  # Will be None - not available on this site
            'rep_votes': rep_votes,  # Will be None - not available on this site
            'total_votes': total_votes,  # Will be None - not available on this site
            'winner': winner
        })

    return parsed_results