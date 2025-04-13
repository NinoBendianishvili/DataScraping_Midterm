# scraper/parser.py
import requests
import time
import re
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any, Tuple
from models.data_models import Party

# --- Fetching & Basic Parsing ---

def fetch_and_parse(url: str, session: requests.Session, delay_seconds: float = 1.0) -> Optional[BeautifulSoup]:
    """ Fetches URL, applies delay, returns BeautifulSoup object. Handles errors. """
    try:
        time.sleep(delay_seconds)
        response = session.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return None

# --- Specific Data Extraction Functions ---

def parse_state_links(soup: BeautifulSoup) -> Dict[str, str]:
    """ Parses the main states list page soup to find state names and URLs. """
    state_links = {}
    if not soup: return state_links
    content_area = soup.find('div', id='primary') or soup.find('main') or soup.body
    if not content_area: return state_links
    links = content_area.select('a[href^="/states/"]')
    for link in links:
        href = link.get('href')
        if href and href.startswith('/states/') and len(href.split('/')) == 3 and href != '/states/':
            state_name = link.get_text(strip=True)
            state_name = re.sub(r'\s*\(.*\)\s*$', '', state_name).strip()
            state_name = re.sub(r'^\s*\d+\s*', '', state_name).strip()
            if state_name and state_name != "States A-Z" and state_name not in state_links:
                state_links[state_name] = href
    return state_links

def parse_state_details(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    """
    Parses state detail page for Electoral Votes and (attempts) Total Population.
    NOTE: Total population is generally NOT available on 270towin state pages.
    """
    details = {'electoral_votes': None, 'total_population': None}
    if not soup: return details

    # --- Electoral Votes ---
    try:
        ev_heading = soup.find('h3', string=lambda t: t and 'ELECTORAL VOTES' in t.upper())
        if ev_heading:
            ev_span = ev_heading.find_next_sibling('span')
            if ev_span:
                ev_text = ev_span.get_text(strip=True)
                if ev_text.isdigit():
                    details['electoral_votes'] = int(ev_text)

        # Fallback Strategy
        if details['electoral_votes'] is None:
            ev_span_alt = soup.find('span', style=lambda s: s and 'font-size:4em' in s)
            if ev_span_alt:
                 ev_text = ev_span_alt.get_text(strip=True)
                 if ev_text.isdigit():
                     details['electoral_votes'] = int(ev_text)
    except Exception as e:
        print(f"Warning: Error extracting electoral votes: {e}")

    # --- Total Population (Attempt - Likely Fails) ---
    # There isn't a consistent selector for this on 270towin state pages.
    # Example: Might look for text like "Population:" if it existed.
    # population_tag = soup.find(string=re.compile(r'Population:\s*([\d,]+)'))
    # if population_tag:
    #     match = re.search(r'Population:\s*([\d,]+)', str(population_tag))
    #     if match:
    #         try:
    #             details['total_population'] = int(match.group(1).replace(',', ''))
    #         except ValueError:
    #             print("Warning: Could not parse found population string.")
    # else:
    #     print("Debug: Total population information not found.") # Expected outcome
    details['total_population'] = None # Explicitly set to None as it's unavailable

    return details


def parse_percentage(text: str) -> Optional[float]:
    """ Helper function to parse percentage strings robustly (0-100). """
    # (Keep the existing robust percentage parser from previous steps)
    if not text: return None
    try:
        cleaned_text = text.strip().replace('%', '')
        cleaned_text = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_text))
        if cleaned_text.count('.') > 1:
             parts = cleaned_text.split('.')
             cleaned_text = parts[0] + '.' + ''.join(parts[1:])
        if not cleaned_text or cleaned_text == '.': return None
        value = float(cleaned_text)
        if 0 <= value <= 100:
            return value
        else:
            return None
    except ValueError:
        return None

def parse_election_results_table(soup: BeautifulSoup, target_years: List[int]) -> List[Dict[str, Any]]:
    """
    Parses the historical results table on a state page.

    Attempts to extract: year, dem_leader, rep_leader, dem_pct, rep_pct, total_votes.
    NOTE: Leaders and Total Votes are generally NOT available in this table structure
          on 270towin.com and will likely remain None.

    Returns:
        List of dicts: [{'year': Y, 'dem_leader': L, 'rep_leader': L, ...}, ...]
    """
    parsed_results = []
    if not soup: return parsed_results

    results_table = soup.find('table', id='recent_elections')
    if not results_table:
        print("Warning: Results table ('recent_elections') not found.")
        return parsed_results

    rows = results_table.select('tbody tr.toggle-row, tr.toggle-row') # Select directly or within tbody

    if not rows:
        print("Warning: No result rows ('toggle-row') found in table.")
        return parsed_results

    for row in rows:
        if row.get('style') and 'display:none' in row.get('style', ''): continue

        cells = row.find_all('td', recursive=False)
        if len(cells) < 2: continue

        year, dem_pct, rep_pct = None, None, None
        dem_leader, rep_leader, total_votes = None, None, None # Initialize as None

        # --- Extract Year ---
        try:
            year_text = cells[0].get_text(strip=True)
            year_match = re.match(r'(\d{4})', year_text)
            if year_match: year = int(year_match.group(1))
        except Exception as e:
            print(f"Warning: Could not parse year: {e}")
            continue
        if year is None or year not in target_years: continue

        # --- Extract Percentages (from Nested Table) ---
        try:
            nested_table = cells[1].find('table')
            if nested_table:
                 nested_row = nested_table.find('tr')
                 if nested_row:
                     nested_cells = nested_row.find_all('td')
                     if len(nested_cells) >= 1: dem_pct = parse_percentage(nested_cells[0].get_text(strip=True))
                     if len(nested_cells) >= 3: rep_pct = parse_percentage(nested_cells[2].get_text(strip=True))
                     # Attempt to find Total Votes (e.g., if it were in a 4th cell) - Unlikely
                     # if len(nested_cells) >= 4:
                     #    tv_text = nested_cells[3].get_text(strip=True).replace(',', '')
                     #    if tv_text.isdigit(): total_votes = int(tv_text)

        except Exception as e:
             print(f"Warning (Year {year}): Error parsing percentages/votes: {e}")

        # --- Attempt to find Leaders (Very Unlikely in this table) ---
        # Example: if leader names were somehow in the first cell with the year
        # dem_leader_match = re.search(r'\(D-([A-Za-z\s]+)\)', year_text)
        # if dem_leader_match: dem_leader = dem_leader_match.group(1).strip()
        # rep_leader_match = re.search(r'\(R-([A-Za-z\s]+)\)', year_text)
        # if rep_leader_match: rep_leader = rep_leader_match.group(1).strip()

        # --- Add parsed data ---
        parsed_results.append({
            'year': year,
            'dem_leader': dem_leader, # Will be None
            'rep_leader': rep_leader, # Will be None
            'dem_pct': dem_pct,
            'rep_pct': rep_pct,
            'total_votes': total_votes # Will be None
        })

    return parsed_results

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