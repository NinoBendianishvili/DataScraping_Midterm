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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/NinoBendianishvili/DataScraping_Midterm
cd DataScraping_Midterm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main scraper:
```bash
python main.py
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

## Contributors

- Nikoloz Topuridze
- Nini Bendianishvili

---

For questions or contributions, please open an issue or submit a pull request.