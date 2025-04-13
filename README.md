# U.S. Election Data Scraper

## Project Overview
This Python project scrapes and analyzes U.S. presidential election data from 270toWin.com, providing insights into historical voting patterns and electoral college trends. The tool collects state-by-state election results, electoral votes, and voting percentages to create a structured dataset for analysis.

## Features

- **State-Level Data Collection**: Gathers electoral votes and historical voting patterns for all 50 states
- **Election Results Analysis**: Extracts Democratic/Republican vote percentages and determines winners
- **Performance Optimized**: Uses concurrent requests to efficiently scrape data
- **Structured Data Output**: Organizes information into clean, analyzable formats

## Requirements

- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - beautifulsoup4
  - requests
  - lxml

## What This Project Does
This tool collects U.S. election information from 270toWin.com and turns it into easy-to-read reports. It shows:
- Which party won each state in past elections
- How voting patterns changed over time
- Important states that often decide elections

## How To Use It

### Quick Start
1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run the scraper:
```bash
python main.py
```

3. Check the `analysis_report` folder for:
- `election_analysis_report.html` - Voting trends and percentages
- `election_static_maps_report.html` - Color-coded election maps

```

The script will:
1. Scrape state electoral vote data
2. Collect historical election results
3. Save the collected data to JSON files
4. Display sample results in the console

## Project Structure

```
/DataScraping_Midterm
│── /analysis_report
│   ├── election_analysis_report.html        # Contains Election Results Analysis
│   └── election_static_maps_report.html     # Contains Map Results Analysis by Year
│── /models
│   └── data_models.py                       # Data structure definitions
│── /scraper
│   ├── collector.py                         # Main scraping logic
│   ├── years.py                             # Years scraping/parsing functions
│   └── parser.py                            # HTML parsing functions
│── /utils
│   ├── analyzer.py                          # Data analysis & visualization
│   ├── file_handler.py                      # Data export functions
│   ├── map_report_template.html             # Election Map Analysis by Year
│   └── report_template.html                 # Election Results Analysis
├── main.py                                  # Entry point
├── requirements.txt                         # Dependencies
└── README.md                                # This file
```

## What's Inside

### Main Files
- `main.py` - Starts everything. Run this to begin scraping.
- `requirements.txt` - Lists all needed Python packages.

### Data Collection
- `scraper/collector.py` - Gets election data from the website
- `scraper/parser.py` - Reads and understands the website's content
- `scraper/years.py` - Handles election year information

### Data Organization
- `models/data_models.py` - Defines how we store election info
- `utils/file_handler.py` - Saves data as CSV and JSON files

### Reports
- `utils/analyzer.py` - Creates charts and maps from the data
- HTML templates in `utils/` - Design the final reports

## How It Works
1. Gets state-by-state election results
2. Saves the raw data
3. Creates easy-to-understand charts and maps
4. Makes HTML reports you can open in any browser

## Tips
- The first run might take 1-2 minutes to get all data
- Change `main.py` to look at different election years
- Open the HTML reports in Chrome/Firefox for best results

## Contributors

- Nikoloz Topuridze
- Nini Bendianishvili