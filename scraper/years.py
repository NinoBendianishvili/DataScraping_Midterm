# scraper/years.py
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
TARGET_PARTIES = ["Democratic", "Republican"] 
BASE_URL = "https://www.270towin.com"

def scrape_election_year(year):
    """
    Fetches and parses election results for a specific year from 270towin.com.
    Returns list of candidate data including winner image URL.
    """
    url = f"{BASE_URL}/{year}-election/"
    logging.info(f"Attempting to scrape data for year {year} from {url}")
    election_data = []
    found_parties_count = 0
    winner_image_url = None

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Improved winner image extraction
        winner_div = soup.find('div', class_='winner-image')
        if winner_div:
            winner_img = winner_div.find('img')
            if winner_img and 'src' in winner_img.attrs:
                winner_image_url = urljoin(BASE_URL, winner_img['src'])
                logging.info(f"Found winner image URL: {winner_image_url}")
            else:
                logging.warning("Winner image found but no src attribute")

        # Alternative approach if the above fails
        if not winner_image_url:
            winner_section = soup.find('div', class_='presidential_candidate_winner')
            if winner_section:
                winner_img = winner_section.find('img')
                if winner_img and 'src' in winner_img.attrs:
                    winner_image_url = urljoin(BASE_URL, winner_img['src'])
                    logging.info(f"Found winner image URL (alt method): {winner_image_url}")

        results_tbody = None
        table_div = soup.find('div', class_='table-responsive')
        if table_div:
            results_tbody = table_div.find('tbody')
        else:
            all_tables = soup.find_all('table')
            for table in all_tables:
                if table.find(string=lambda text: "Democratic" in text or "Republican" in text):
                    results_tbody = table.find('tbody')
                    if results_tbody:
                        logging.info("Found results table via fallback search.")
                        break

        if not results_tbody:
            logging.warning(f"Could not find the results table body for year {year}.")
            return []

        rows = results_tbody.find_all('tr')
        winning_party = None

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                try:
                    party = cells[3].get_text(strip=True)

                    if party in TARGET_PARTIES:
                        name = cells[2].get_text(strip=True)
                        electoral_votes = cells[4].get_text(strip=True)
                        popular_votes = cells[5].get_text(strip=True)

                        name = name.split('(')[0].strip()

                        candidate_data = {
                            "party": party,
                            "leader": name,
                            "electoral_votes": electoral_votes,
                            "popular_votes": popular_votes
                        }

                        # Check if this is the winning candidate
                        if "winner" in row.get('class', []):
                            winning_party = party
                            candidate_data["winner_image_url"] = winner_image_url
                            logging.info(f"Identified winner: {name} ({party})")

                        election_data.append(candidate_data)
                        found_parties_count += 1
                        logging.info(f"Found data for {party} candidate: {name}")

                        if found_parties_count == len(TARGET_PARTIES):
                            break

                except IndexError:
                    continue
                except Exception as cell_e:
                    logging.error(f"Error processing row cells for year {year}: {cell_e} | Row HTML: {row}")

        # If we have a winner but didn't find the image through normal methods
        if winning_party and not winner_image_url:
            logging.warning(f"Winner identified ({winning_party}) but no image URL found")
            # Try one last method - look for candidate images in the page
            candidate_images = soup.find_all('img', class_='candidate-image')
            for img in candidate_images:
                if winning_party.lower() in img.get('alt', '').lower():
                    winner_image_url = urljoin(BASE_URL, img['src'])
                    logging.info(f"Found winner image via candidate-image class: {winner_image_url}")
                    # Update the winner's data
                    for data in election_data:
                        if data['party'] == winning_party:
                            data['winner_image_url'] = winner_image_url
                    break

        if not election_data:
            logging.warning(f"Extracted data list is empty for year {year}. Check table structure.")
        elif found_parties_count < len(TARGET_PARTIES):
            logging.warning(f"Only found data for {found_parties_count}/{len(TARGET_PARTIES)} target parties for year {year}.")


    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error fetching URL {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection Error fetching URL {url}: {e}")
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout fetching URL {url}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while scraping year {year}: {e}")

    return election_data
