# scraper/parser.py
import requests
import time
import re
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any, Tuple
from models.data_models import Party

def fetch_and_parse(url: str, session: requests.Session, delay_seconds: float = 0.5) -> Optional[BeautifulSoup]:
    """Optimized fetch function with timeout handling"""
    try:
        time.sleep(delay_seconds)
        response = session.get(url, timeout=15)
        response.raise_for_status()
        try:
            return BeautifulSoup(response.content, 'lxml')
        except ImportError:
            return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {str(e)[:100]}...")
        return None
    except Exception as e:
        print(f"Error parsing URL {url}: {str(e)[:100]}...")
        return None

def parse_state_links(soup: BeautifulSoup) -> Dict[str, str]:
    """Parses the main states list page soup to find state names and URLs."""
    state_links = {}
    if not soup:
        print("Warning: No soup object provided to parse_state_links.")
        return state_links

    content_area = soup.find('main', id='main') or soup.find('div', id='primary') or soup.body
    if not content_area:
        print("Warning: Could not find main content area (main#main or div#primary) on states page.")
        return state_links

    heading = content_area.find(['h2', 'h3'], string=re.compile(r'States\s+A-Z', re.IGNORECASE))
    target_list = None
    if heading:
        target_list = heading.find_next_sibling('ul')

    if not target_list:
         all_lists = content_area.find_all('ul')
         for ul in all_lists:
             potential_links = ul.select('li > a[href^="/states/"]')
             if potential_links and len(potential_links[0]['href'].split('/')) == 3:
                 target_list = ul
                 print("Debug: Found state link list using fallback search (no .html check).")
                 break

    if not target_list:
        print("Warning: Could not find the specific <ul> containing state links.")
        links = content_area.select('a[href^="/states/"]')
        print(f"Debug: Last resort search found {len(links)} potential links in content_area.")
        if not links:
            return state_links
    else:
        links = target_list.select('li > a[href^="/states/"]')
        print(f"Debug: Found {len(links)} potential links in the targeted list (no .html check).")

    for link in links:
        href = link.get('href')
        if href and href.startswith('/states/') and len(href.split('/')) == 3:
            if href == '/states/' or href == '/states': continue
            state_name = link.get_text(strip=True)
            state_name = re.sub(r'\s*\(\s*\d+\s*EV\s*\)\s*$', '', state_name).strip()
            state_name = re.sub(r'^\s*\d+\s*', '', state_name).strip()
            if state_name and state_name not in state_links:
                 if len(state_name) < 30 and not state_name.isdigit():
                    state_links[state_name] = href

    if "District of Columbia" not in state_links:
         dc_link = content_area.find('a', href='/states/district_of_columbia')
         if dc_link:
             dc_name = dc_link.get_text(strip=True)
             dc_name = re.sub(r'\s*\(\s*\d+\s*EV\s*\)\s*$', '', dc_name).strip()
             state_links[dc_name] = "/states/district_of_columbia"
             print("Debug: Added District of Columbia link explicitly (no .html).")

    if not state_links:
         print("Warning: After all attempts, failed to extract any valid state links.")
    else:
         print(f"Debug: Final state link count: {len(state_links)}")

    return state_links

def parse_state_details(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    """Parses state detail page for Electoral Votes."""
    details = {'electoral_votes': None, 'total_population': None}
    if not soup: return details

    try:
        ev_span_large = soup.find('span', class_='ev')
        if ev_span_large and ev_span_large.get_text(strip=True).isdigit():
             details['electoral_votes'] = int(ev_span_large.get_text(strip=True))
        else:
             ev_heading = soup.find(['h2','h3'], string=lambda t: t and 'ELECTORAL VOTES' in t.upper())
             if ev_heading:
                 heading_text = ev_heading.get_text(strip=True)
                 match = re.match(r'(\d+)\s+ELECTORAL VOTES', heading_text)
                 if match:
                     details['electoral_votes'] = int(match.group(1))
                 else:
                     ev_span = ev_heading.find_next_sibling('span')
                     if ev_span and ev_span.get_text(strip=True).isdigit():
                         details['electoral_votes'] = int(ev_span.get_text(strip=True))

        if details['electoral_votes'] is None:
            ev_span_alt = soup.find('span', style=lambda s: s and 'font-size:4em' in s.lower())
            if ev_span_alt and ev_span_alt.get_text(strip=True).isdigit():
                 details['electoral_votes'] = int(ev_span_alt.get_text(strip=True))

    except Exception as e:
        print(f"Warning: Error extracting electoral votes: {e}")

    details['total_population'] = None

    return details

def parse_percentage(text: str) -> Optional[float]:
    """Helper function to parse percentage strings robustly (0-100)."""
    if not text: return None
    try:
        cleaned_text = text.strip().replace('%', '').replace('\xa0', '')
        cleaned_text = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_text))
        if cleaned_text.count('.') > 1:
             parts = cleaned_text.split('.')
             cleaned_text = parts[0] + '.' + ''.join(parts[1:])
        if not cleaned_text or cleaned_text == '.': return None
        value = float(cleaned_text)
        if 0 <= value <= 100.1:
            return round(min(value, 100.0), 2)
        else:
            print(f"Warning: Parsed percentage '{value}' out of range (0-100). Text was: '{text}'")
            return None
    except ValueError:
        return None

def parse_election_results_table(soup: BeautifulSoup, target_years: List[int]) -> List[Dict[str, Any]]:
    """Parses the historical results table on a state page for Year, Percentages, and Winner."""
    parsed_results = []
    if not soup: return parsed_results

    results_table = soup.find('table', id='recent_elections')
    if not results_table:
        results_table = soup.find('table', class_='state-results-table')
        if not results_table:
             print("Warning: Results table ('recent_elections' or fallback) not found.")
             return parsed_results

    rows = results_table.find_all('tr', class_='toggle-row')
    if not rows:
         tbody = results_table.find('tbody')
         if tbody:
             rows = [r for r in tbody.find_all('tr', recursive=False) if len(r.find_all('td', recursive=False)) >= 2]

    if not rows:
        print("Warning: No suitable result rows found in table.")
        return parsed_results

    for row in rows:
        style = row.get('style', '')
        if 'display' in style and 'none' in style: continue

        cells = row.find_all('td', recursive=False)
        if len(cells) < 2: continue

        year, dem_pct, rep_pct = None, None, None
        winner = None

        try:
            year_cell_text = cells[0].get_text(strip=True)
            year_match = re.search(r'(\d{4})', year_cell_text)
            if year_match:
                year = int(year_match.group(1))
            else:
                year_tag = cells[0].find(['span', 'strong', 'a'])
                if year_tag:
                     year_match = re.search(r'(\d{4})', year_tag.get_text(strip=True))
                     if year_match: year = int(year_match.group(1))

        except Exception as e:
            print(f"Warning: Could not parse year from cell: {cells[0].prettify()[:100]}... Error: {e}")
            continue

        if year is None or year not in target_years: continue

        try:
            results_cell = cells[1]
            nested_table = results_cell.find('table')
            if nested_table:
                 nested_row = nested_table.find('tr')
                 if nested_row:
                     nested_cells = nested_row.find_all('td')
                     if len(nested_cells) >= 1:
                         dem_pct = parse_percentage(nested_cells[0].get_text(strip=True))
                     if len(nested_cells) >= 3:
                         rep_pct = parse_percentage(nested_cells[2].get_text(strip=True))
            else:
                 cell_text = results_cell.get_text(separator='|', strip=True)
                 dem_match = re.search(r'D:?\s*([\d.]+)%', cell_text)
                 rep_match = re.search(r'R:?\s*([\d.]+)%', cell_text)
                 if dem_match: dem_pct = parse_percentage(dem_match.group(1))
                 if rep_match: rep_pct = parse_percentage(rep_match.group(1))

        except Exception as e:
             print(f"Warning (Year {year}): Error parsing percentages/winner structure: {e}")

        if dem_pct is not None and rep_pct is not None:
            if dem_pct > rep_pct:
                winner = Party.DEMOCRATIC
            elif rep_pct > dem_pct:
                winner = Party.REPUBLICAN
            else:
                winner = Party.OTHER
        elif dem_pct is not None or rep_pct is not None:
             winner = Party.OTHER

        parsed_results.append({
            'year': year,
            'dem_pct': dem_pct,
            'rep_pct': rep_pct,
            'winner': winner
        })

    return parsed_results
