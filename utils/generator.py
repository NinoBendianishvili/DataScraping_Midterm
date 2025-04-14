import json
from collections import defaultdict

def generate_static_maps_report(input_json_path: str, output_html_path: str):
    with open(input_json_path, "r") as f:
        election_data = json.load(f)

    election_by_year = defaultdict(lambda: {"dem": [], "rep": []})
    state_abbr = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
        "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
        "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
        "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
        "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
    }

    for record in election_data:
        year = record["year_info"]["year"]
        state = record["state_info"]["state_name"]
        abbr = state_abbr.get(state)
        if not abbr:
            continue
        winner = record["state_election_details"]["state_winner"]
        if winner == "Democratic":
            election_by_year[year]["dem"].append(abbr)
        elif winner == "Republican":
            election_by_year[year]["rep"].append(abbr)

    # Prepare HTML content
    plots = ""
    for year in sorted(election_by_year):
        plots += f"""
        <div class="plot-container">
            <h2>{year} Election Map</h2>
            <div id="map-{year}" class="plotly-graph-div"></div>
        </div>
        """

    final_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>U.S. Presidential Election Results (2000-2020)</title>
        <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                padding: 20px;
            }}
            .super-container {{
                display: none;
                margin: 30px auto;
                max-width: 1000px;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .super-container.active {{
                display: block;
            }}
            h1, h2 {{
                text-align: center;
            }}
            #year-selector {{
                display: block;
                margin: 0 auto 30px auto;
                font-size: 16px;
                padding: 8px;
            }}
        </style>
    </head>
    <body>
        <h1>U.S. Presidential Election Results by State (2000-2020)</h1>

        <label for="year-selector" style="text-align:center;display:block;margin-bottom:10px;font-weight:bold;">Select a year:</label>
        <select id="year-selector">
            {''.join([f'<option value="{year}">{year}</option>' for year in sorted(election_by_year)])}
        </select>

        {''.join([
            f'''
            <div class="super-container" id="container-{year}">
                <h2>{year} Election Map</h2>
                <div id="map-{year}" class="plotly-graph-div"></div>
            </div>
            ''' for year in sorted(election_by_year)
        ])}

        <p style="text-align:center;font-style:italic;color:#6c757d;">
            Note: Colors represent winning party (Red = Republican, Blue = Democrat)
        </p>

        <script>
            const electionData = {json.dumps(election_by_year)};
            const plottedYears = new Set();

            const selector = document.getElementById("year-selector");
            const containers = document.querySelectorAll(".super-container");

            function plotMap(year) {{
                if (plottedYears.has(year)) return;

                const data = electionData[year];
                const plotData = [
                    {{
                        type: 'choropleth',
                        locationmode: 'USA-states',
                        locations: data.dem,
                        z: Array(data.dem.length).fill(0),
                        colorscale: [[0, 'rgb(0, 0, 255)'], [1, 'rgb(0, 0, 255)']],
                        showscale: false,
                        name: 'Democrat'
                    }},
                    {{
                        type: 'choropleth',
                        locationmode: 'USA-states',
                        locations: data.rep,
                        z: Array(data.rep.length).fill(1),
                        colorscale: [[0, 'rgb(255, 0, 0)'], [1, 'rgb(255, 0, 0)']],
                        showscale: false,
                        name: 'Republican'
                    }}
                ];
                const layout = {{
                    title: year + " Presidential Election",
                    geo: {{
                        scope: 'usa',
                        projection: {{ type: 'albers usa' }},
                        showlakes: true,
                        lakecolor: 'rgb(255,255,255)'
                    }},
                    margin: {{ t: 50, l: 0, r: 0, b: 0 }}
                }};
                Plotly.newPlot("map-" + year, plotData, layout);
                plottedYears.add(year);
            }}

            function updateVisibleYear(selectedYear) {{
                containers.forEach(c => c.classList.remove("active"));
                const active = document.getElementById("container-" + selectedYear);
                if (active) {{
                    active.classList.add("active");
                    plotMap(selectedYear);
                }}
            }}

            selector.addEventListener("change", (e) => {{
                updateVisibleYear(e.target.value);
            }});

            // Initial load
            updateVisibleYear(selector.value);
        </script>
    </body>
    </html>
    """


    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(final_html)
