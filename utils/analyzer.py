# analyzer.py
import pandas as pd
import os
import plotly.express as px
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import List, Dict, Union, Optional
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_CSV_DIR = "output"
INPUT_CSV_FILENAME = "election_results_combined.csv"
OUTPUT_DIR = "analysis_report"
OUTPUT_BAR_CHART_HTML_FILENAME = "election_analysis_report.html"
OUTPUT_STATIC_MAPS_HTML_FILENAME = "election_static_maps_report.html"
TEMPLATE_DIR = "utils"
BAR_CHART_TEMPLATE_NAME = "report_template.html"
STATIC_MAPS_TEMPLATE_NAME = "map_report_template.html"

PARTY_COLORS = {
    'Democratic': 'blue',
    'Republican': 'red'
}

DEM_NAT_VOTE_COL = 'dem_national_votes'
REP_NAT_VOTE_COL = 'rep_national_votes'
DEM_STATE_PCT_COL = 'dem_state_percentage'
REP_STATE_PCT_COL = 'rep_state_percentage'
DEM_LEADER_COL = 'dem_leader'
REP_LEADER_COL = 'rep_leader'
YEAR_COL = 'year'
STATE_NAME_COL = 'state_name'
WINNER_COL = 'state_winner'
WINNER_IMAGE_COL = 'winner_image_url'

def load_data(filepath: str) -> Optional[pd.DataFrame]:
    logger.info(f"Attempting to load data from: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Error: Input CSV file not found at {filepath}")
        return None
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Successfully loaded data with shape: {df.shape}")
        logger.debug(f"CSV Columns loaded: {df.columns.tolist()}")

        required_cols = [
            YEAR_COL, DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL,
            STATE_NAME_COL, DEM_STATE_PCT_COL, REP_STATE_PCT_COL, WINNER_COL,
            DEM_LEADER_COL, REP_LEADER_COL, WINNER_IMAGE_COL
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in CSV: {missing_cols}")
            return None

        numeric_cols = [DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL, DEM_STATE_PCT_COL, REP_STATE_PCT_COL]
        logger.info("Converting relevant columns to numeric...")
        for col in numeric_cols:
            if col in df.columns:
                original_dtype = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].isnull().any():
                     logger.warning(f"Column '{col}' contained non-numeric values -> NaN. Original type: {original_dtype}")

        vote_cols = [DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL]
        rows_before_drop = len(df)
        logger.info(f"Dropping rows where national votes ({vote_cols}) are missing...")
        df.dropna(subset=vote_cols, inplace=True)
        rows_after_drop = len(df)
        if rows_before_drop > rows_after_drop:
             logger.warning(f"Dropped {rows_before_drop - rows_after_drop} rows due to missing national vote data.")

        df[WINNER_COL] = df[WINNER_COL].astype(str).str.strip()
        logger.info(f"Unique raw values in '{WINNER_COL}' before cleaning None/NA: {df[WINNER_COL].unique()}")
        df[WINNER_COL] = df[WINNER_COL].replace({'nan': None, '': None, 'N/A': None})
        df.dropna(subset=[WINNER_COL], inplace=True)
        logger.info(f"Unique values in '{WINNER_COL}' after cleaning None/NA and dropping: {df[WINNER_COL].dropna().unique()}") # Use dropna() for unique
        valid_winners = list(PARTY_COLORS.keys())
        initial_rows = len(df)
        df = df[df[WINNER_COL].isin(valid_winners)].copy() # Use .copy() for explicit copy
        if len(df) < initial_rows:
             removed_count = initial_rows - len(df)
             logger.warning(f"Removed {removed_count} rows with unexpected winner values not in {valid_winners}.")

        df[DEM_LEADER_COL] = df[DEM_LEADER_COL].fillna('N/A').astype(str).str.strip()
        df[REP_LEADER_COL] = df[REP_LEADER_COL].fillna('N/A').astype(str).str.strip()
        df[WINNER_IMAGE_COL] = df[WINNER_IMAGE_COL].fillna('').astype(str).str.strip()

        df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors='coerce').astype('Int64')
        if df[YEAR_COL].isnull().any():
             logger.warning("Found missing or non-numeric values in 'year' column. Rows with invalid years will be excluded.")
             df.dropna(subset=[YEAR_COL], inplace=True)

        df[STATE_NAME_COL] = df[STATE_NAME_COL].astype(str).str.strip()
        df.dropna(subset=[STATE_NAME_COL], inplace=True) # Drop if state name is missing


        logger.info(f"Data types converted and cleaning done. Final DataFrame shape: {df.shape}")
        if not df.empty:
            logger.debug("First 5 rows of cleaned data:\n%s", df.head().to_string())
        else:
            logger.warning("DataFrame is empty after cleaning.")
        return df
    except Exception as e:
        logger.error(f"An error occurred during data loading or cleaning: {e}", exc_info=True)
        return None

def create_national_plot(df: pd.DataFrame) -> Optional[str]:
    logger.info("Generating national trends plot (bar chart)...")
    if df.empty or not {DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL}.issubset(df.columns):
        logger.warning("Input DataFrame empty or missing required national vote columns for national plot.")
        return "<p>No data available for national plot.</p>"
    try:
        vote_cols = [DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL]
        national_votes = df.groupby(YEAR_COL)[vote_cols].first().reset_index()

        national_votes[DEM_NAT_VOTE_COL] = pd.to_numeric(national_votes[DEM_NAT_VOTE_COL], errors='coerce')
        national_votes[REP_NAT_VOTE_COL] = pd.to_numeric(national_votes[REP_NAT_VOTE_COL], errors='coerce')
        national_votes.dropna(subset=vote_cols, inplace=True) # Drop if conversion failed

        national_votes['total_votes'] = national_votes[DEM_NAT_VOTE_COL] + national_votes[REP_NAT_VOTE_COL]
        national_votes = national_votes[national_votes['total_votes'] > 0].copy() # Filter zero votes

        if national_votes.empty:
            logger.warning("No valid national vote data found after filtering zero total votes.")
            return "<p>No valid national vote data to plot after filtering.</p>"

        national_votes['Democratic (%)'] = (national_votes[DEM_NAT_VOTE_COL] / national_votes['total_votes']) * 100
        national_votes['Republican (%)'] = (national_votes[REP_NAT_VOTE_COL] / national_votes['total_votes']) * 100

        plot_data = national_votes.melt(
            id_vars=[YEAR_COL], value_vars=['Democratic (%)', 'Republican (%)'],
            var_name='Party', value_name='Percentage'
        )
        plot_data['Party'] = plot_data['Party'].str.replace(r' \(\%\)', '', regex=True)

        fig = px.bar(
            plot_data, x=YEAR_COL, y='Percentage', color='Party', barmode='group',
            title="National Popular Vote Share (%) by Year",
            labels={'Percentage': 'Vote Percentage (%)', YEAR_COL: 'Election Year'},
            text_auto='.1f',
            color_discrete_map={'Democratic': PARTY_COLORS['Democratic'], 'Republican': PARTY_COLORS['Republican']} # Explicit map
        )
        fig.update_layout(yaxis_range=[0, 100])
        fig.update_traces(textposition='outside')
        plot_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
        logger.info("National trends bar chart created successfully.")
        return plot_div
    except Exception as e:
        logger.error(f"Failed to create national bar chart: {e}", exc_info=True)
        return "<p>An error occurred while generating the national bar chart.</p>"


def create_state_plot(state_df: pd.DataFrame, state_name: str) -> Optional[str]:
    logger.debug(f"Generating bar chart for state: {state_name}")
    if state_df.empty:
        logger.warning(f"Input DataFrame for state bar chart ({state_name}) is empty.")
        return f"<p>No data provided for state bar chart: {state_name}.</p>"

    pct_cols = [DEM_STATE_PCT_COL, REP_STATE_PCT_COL]
    if not all(col in state_df.columns for col in pct_cols):
        missing = [col for col in pct_cols if col not in state_df.columns]
        logger.error(f"Missing state percentage columns for state bar chart ({state_name}): {missing}")
        return f"<p>Missing data columns for {state_name} bar chart.</p>"

    try:
        state_plot_data = state_df[[YEAR_COL] + pct_cols].copy()

        state_plot_data[DEM_STATE_PCT_COL] = pd.to_numeric(state_plot_data[DEM_STATE_PCT_COL], errors='coerce')
        state_plot_data[REP_STATE_PCT_COL] = pd.to_numeric(state_plot_data[REP_STATE_PCT_COL], errors='coerce')

        state_plot_data.rename(columns={
            DEM_STATE_PCT_COL: 'Democratic', REP_STATE_PCT_COL: 'Republican'
        }, inplace=True)

        state_plot_data.dropna(subset=['Democratic', 'Republican'], how='all', inplace=True)

        if state_plot_data.empty:
            logger.warning(f"No valid percentage data rows to plot for state bar chart: {state_name} after dropping NaNs.")
            return f"<p>No graphable percentage data available for {state_name} bar chart.</p>"

        state_plot_data = state_plot_data.melt(
            id_vars=[YEAR_COL], value_vars=['Democratic', 'Republican'],
            var_name='Party', value_name='Percentage'
        )

        state_plot_data['Percentage'] = pd.to_numeric(state_plot_data['Percentage'], errors='coerce')
        # Optional: Drop rows if percentage became NaN during melt/conversion (shouldn't happen often)
        state_plot_data.dropna(subset=['Percentage'], inplace=True)

        if state_plot_data.empty:
             logger.warning(f"No numeric percentage values found for {state_name} after melt.")
             return f"<p>Could not plot percentages for {state_name}.</p>"

        fig = px.bar(
            state_plot_data, x=YEAR_COL, y='Percentage', color='Party', barmode='group',
            title=f"{state_name} Presidential Vote Share (%) by Year",
            labels={'Percentage': 'State Vote Percentage (%)', YEAR_COL: 'Election Year'},
            text_auto='.1f',
            color_discrete_map={'Democratic': PARTY_COLORS['Democratic'], 'Republican': PARTY_COLORS['Republican']} # Explicit map
        )
        fig.update_layout(yaxis_range=[0, 100])
        fig.update_traces(textposition='outside')
        plot_div = fig.to_html(full_html=False, include_plotlyjs=False)
        logger.debug(f"Bar chart created successfully for state: {state_name}")
        return plot_div
    except Exception as e:
        logger.error(f"Failed to create bar chart for state {state_name}: {e}", exc_info=True)
        return f"<p>Error generating bar chart for {state_name}.</p>"

def generate_bar_chart_html_report(national_plot_div: Optional[str], state_plot_divs: Dict[str, str], years: List[int], output_path: str):
    logger.info(f"Generating bar chart HTML report to: {output_path}")
    if not national_plot_div and not state_plot_divs:
         logger.warning("Both national and state bar chart data are missing. Bar chart HTML report will be mostly empty.")
    try:
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(['html', 'xml']))
        template = env.get_template(BAR_CHART_TEMPLATE_NAME) # Assumes bar chart template still exists
        logger.info(f"Loaded Jinja template: {BAR_CHART_TEMPLATE_NAME}")
        years_str = f"{min(years)} - {max(years)}" if years else "N/A"
        national_plot_html = national_plot_div if national_plot_div and "<p>" not in national_plot_div else \
                             "<p>National bar chart could not be generated. Check logs and input data.</p>"

        valid_state_plots = {k: v for k, v in state_plot_divs.items() if v and "<p>" not in v}
        if len(valid_state_plots) < len(state_plot_divs):
            logger.warning(f"Excluded {len(state_plot_divs) - len(valid_state_plots)} state bar charts due to generation errors.")

        context = {
            'national_plot_div': national_plot_html,
            'state_plot_divs': valid_state_plots, # Pass only valid plots
            'years_analyzed': years_str
        }
        logger.debug("Context prepared for bar chart Jinja template.")
        html_content = template.render(context)
        logger.info("Bar chart HTML template rendered successfully.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True) # Ensure dir exists
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Bar chart HTML report successfully generated and saved at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate bar chart HTML report: {e}", exc_info=True)



def create_static_map(df_year: pd.DataFrame, year: int, include_js: bool = False) -> Optional[str]:
    """Creates a static Plotly choropleth map for a single election year."""
    logger.info(f"Generating static map for year: {year}...")

    map_cols = [STATE_NAME_COL, WINNER_COL, DEM_LEADER_COL, REP_LEADER_COL, WINNER_IMAGE_COL]
    if df_year.empty or not all(col in df_year.columns for col in map_cols):
        missing = [col for col in map_cols if col not in df_year.columns]
        logger.error(f"Year {year} DataFrame empty or missing required columns for map: {missing}")
        return f"<p>No or incomplete data for map in year {year}. Missing: {missing}</p>"

    df_year = df_year.copy() # Avoid SettingWithCopyWarning
    df_year[WINNER_COL] = df_year[WINNER_COL].astype(str).str.strip()
    valid_winners = list(PARTY_COLORS.keys())
    df_year = df_year[df_year[WINNER_COL].isin(valid_winners)]

    if df_year.empty:
        logger.warning(f"No valid states found for map in year {year} after filtering winners.")
        return f"<p>No states with valid winners ({valid_winners}) found for {year}.</p>"

    logger.debug(f"Data shape for year {year} map: {df_year.shape}")
    logger.debug(f"Unique winners for year {year} map: {df_year[WINNER_COL].unique()}")

    try:
        fig = px.choropleth(
            df_year,
            locations=STATE_NAME_COL,
            locationmode='USA-states',
            color=WINNER_COL,
            hover_name=STATE_NAME_COL,
            hover_data={
                WINNER_COL: True,
                DEM_LEADER_COL: True,
                REP_LEADER_COL: True,
                WINNER_IMAGE_COL: True
            },
            color_discrete_map=PARTY_COLORS, # Map Dem/Rep strings to blue/red
            scope='usa',
            title=f"Election Results - {year}" # Simple title for the individual map
        )

        fig.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0}, # Adjust top margin for title
            geo=dict(bgcolor= 'rgba(0,0,0,0)'),
            legend_title_text='State Winner'
        )

        plot_div = fig.to_html(full_html=False, include_plotlyjs=include_js)

        logger.info(f"Static map created successfully for year: {year}")
        return plot_div

    except Exception as e:
        logger.error(f"Failed to create static map for year {year}: {e}", exc_info=True)
        return f"<p>An error occurred generating the map for {year}.</p>"

def generate_bar_chart_html_report(national_plot_div: Optional[str], state_plot_divs: Dict[str, str], years: List[int], output_path: str):
    logger.info(f"Generating bar chart HTML report to: {output_path}")
    if not national_plot_div and not state_plot_divs:
         logger.warning("Both national and state bar chart data are missing. Bar chart HTML report will be mostly empty.")
    try:
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(['html', 'xml']))
        template = env.get_template(BAR_CHART_TEMPLATE_NAME)
        logger.info(f"Loaded Jinja template: {BAR_CHART_TEMPLATE_NAME}")
        years_str = f"{min(years)} - {max(years)}" if years else "N/A"
        national_plot_html = national_plot_div if national_plot_div and "<p>" not in national_plot_div else \
                             "<p>National bar chart could not be generated. Check logs and input data.</p>"

        valid_state_plots = {k: v for k, v in state_plot_divs.items() if v and "<p>" not in v}
        if len(valid_state_plots) < len(state_plot_divs):
            logger.warning(f"Excluded {len(state_plot_divs) - len(valid_state_plots)} state bar charts due to generation errors.")

        context = {
            'national_plot_div': national_plot_html,
            'state_plot_divs': valid_state_plots,
            'years_analyzed': years_str
        }
        logger.debug("Context prepared for bar chart Jinja template.")
        html_content = template.render(context)
        logger.info("Bar chart HTML template rendered successfully.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Bar chart HTML report successfully generated and saved at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate bar chart HTML report: {e}", exc_info=True)

def generate_static_maps_report(map_divs: Dict[int, str], years: List[int], output_path: str):
    """Generates an HTML report containing multiple static maps."""
    logger.info(f"Generating static maps HTML report to: {output_path}")

    if not map_divs:
         logger.warning("No map divs provided. Static maps HTML report will be empty.")

    try:
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(['html', 'xml']))
        template = env.get_template(STATIC_MAPS_TEMPLATE_NAME)
        logger.info(f"Loaded Jinja template: {STATIC_MAPS_TEMPLATE_NAME}")

        years_str = f"{min(years)} - {max(years)}" if years else "N/A"
        years_sorted = sorted(map_divs.keys()) # Ensure maps are ordered by year

        context = {
            'map_divs': map_divs,
            'years_sorted': years_sorted,
            'years_analyzed_str': years_str
        }
        logger.debug("Context prepared for static maps Jinja template.")
        html_content = template.render(context)
        logger.info("Static maps HTML template rendered successfully.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True) # Ensure dir exists
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Static maps HTML report successfully generated and saved at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate static maps HTML report: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("="*30)
    logger.info("Starting Election Analysis Script (Bar Charts & Static Maps)")
    logger.info("="*30)
    input_csv_path = os.path.abspath(os.path.join(INPUT_CSV_DIR, INPUT_CSV_FILENAME))
    output_bar_chart_html_path = os.path.abspath(os.path.join(OUTPUT_DIR, OUTPUT_BAR_CHART_HTML_FILENAME))
    output_static_maps_html_path = os.path.abspath(os.path.join(OUTPUT_DIR, OUTPUT_STATIC_MAPS_HTML_FILENAME))
    template_dir_path = os.path.abspath(TEMPLATE_DIR)
    bar_template_path = os.path.join(template_dir_path, BAR_CHART_TEMPLATE_NAME)
    static_maps_template_path = os.path.join(template_dir_path, STATIC_MAPS_TEMPLATE_NAME)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    logger.info(f"Input CSV path: {input_csv_path}")
    logger.info(f"Output Bar Chart HTML: {output_bar_chart_html_path}")
    logger.info(f"Output Static Maps HTML: {output_static_maps_html_path}") # Updated log
    logger.info(f"Template directory: {template_dir_path}")

    templates_exist = True
    if not os.path.exists(bar_template_path):
         logger.error(f"Bar chart template file not found at '{bar_template_path}'.")
         templates_exist = False
    if not os.path.exists(static_maps_template_path): # Check new template
         logger.error(f"Static maps template file not found at '{static_maps_template_path}'.")
         templates_exist = False

    if not templates_exist:
        logger.error("Analysis stopped: Missing one or more HTML template files.")
    else:
        df_loaded = load_data(input_csv_path)

        if df_loaded is not None and not df_loaded.empty:
            df_loaded[YEAR_COL] = df_loaded[YEAR_COL].astype(int)
            analyzed_years = sorted(df_loaded[YEAR_COL].unique().tolist())
            logger.info(f"Years found in cleaned data: {analyzed_years}")

            logger.info("-" * 20 + " Generating Bar Chart Report " + "-" * 20)
            national_bar_div = create_national_plot(df_loaded.copy())
            state_bar_divs = {}
            if STATE_NAME_COL in df_loaded.columns:
                states = sorted(df_loaded[STATE_NAME_COL].unique())
                logger.info(f"Processing {len(states)} states for bar charts...")
                processed_bar_states = 0
                for state in states:
                    state_df = df_loaded[df_loaded[STATE_NAME_COL] == state].copy()
                    # Pass include_js=False as national plot includes it
                    state_div = create_state_plot(state_df, state)
                    if state_div:
                        state_bar_divs[state] = state_div
                        processed_bar_states += 1
                logger.info(f"Successfully generated bar chart data for {processed_bar_states}/{len(states)} states.")
            else:
                logger.error(f"Column '{STATE_NAME_COL}' not found. Skipping state bar charts.")
            generate_bar_chart_html_report(national_bar_div, state_bar_divs, analyzed_years, output_bar_chart_html_path)

            logger.info("-" * 20 + " Generating Static Maps Report " + "-" * 20)
            static_map_divs = {}
            include_js_for_map = True
            for year in analyzed_years:
                df_year = df_loaded[df_loaded[YEAR_COL] == year].copy()
                map_div = create_static_map(df_year, year, include_js=include_js_for_map)
                if map_div: # Only store successfully generated maps
                    static_map_divs[year] = map_div
                    include_js_for_map = False # Don't include JS for subsequent maps

            generate_static_maps_report(static_map_divs, analyzed_years, output_static_maps_html_path)

        elif df_loaded is None:
            logger.error("Analysis stopped: Data loading failed.")
        else: # df_loaded is not None but is empty
             logger.error("Analysis stopped: Data loaded but resulted in an empty DataFrame after cleaning/filtering.")
             generate_bar_chart_html_report(None, {}, [], output_bar_chart_html_path)
             generate_static_maps_report({}, [], output_static_maps_html_path)


    logger.info("="*30)
    logger.info("Election analysis finished.")
    logger.info("="*30)
    