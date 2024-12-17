######### =========== GDP REPORT --MAIN =========== #########

import streamlit as st
import datetime

from workhorses.gdp_report.data_fetcher import fetch_all_data
from workhorses.gdp_report.data_processor import *
from workhorses.gdp_report.visualizations import generate_charts
from workhorses.gdp_report.report_export import generate_word_doc, generate_html_report


# Constants
BEA_API_KEY = st.secrets["BEA_API_KEY"]
today = datetime.datetime.today()
week_ago = today - datetime.timedelta(days=7)
week_ago_debttopenny = week_ago.strftime("%Y-%m-%d")

def main():
    print("\nStarting GDP Report Generation...")
    
    ## Fetch Data  
    pct_change_raw, gdp_raw, contributors_raw, debt_df = fetch_all_data(
        BEA_API_KEY, week_ago_debttopenny
        )

    CURRENT_QUARTER = pct_change_raw.TimePeriod.max()
    PREVIOUS_QUARTER = CURRENT_QUARTER[:-1] + str(int(CURRENT_QUARTER[-1]) - 1)
    CURRENT_GDP_GROWTH = pct_change_raw[pct_change_raw.TimePeriod == CURRENT_QUARTER].DataValue.values[0]
    
    
    ## Process Data
    
    # Release info
    release_stage, current_quarter_text = scrape_release_info()
    revision_data, original = scrape_revisions_data(CURRENT_QUARTER, release_stage)
    
    # Overview text
    overview_text = generate_overview_text(pct_change_raw, gdp_raw, debt_df, CURRENT_QUARTER, PREVIOUS_QUARTER, release_stage, current_quarter_text)
    
    # Contributors 
    main_contributors_df, contributors_expanded_df, contributors_chart_data, main_contributors_line_number_dict = clean_contributors_data(contributors_raw, CURRENT_QUARTER)
    contributors_text = generate_contributors_text(main_contributors_df, contributors_expanded_df, main_contributors_line_number_dict, CURRENT_GDP_GROWTH)
    
    # Changes text
    changes_text = generate_changes_text(pct_change_raw, CURRENT_QUARTER)

    # Revision text
    if release_stage.lower() != "advance estimate":
        revision_data = clean_revisions_data(revision_data)
        revision_text = generate_revisions_text(revision_data, release_stage, original)
    else:
        revision_text = None

    ## Generate Visualizations
    generate_charts(pct_change_raw, contributors_chart_data, revision_data, CURRENT_QUARTER, PREVIOUS_QUARTER, release_stage, original)

    ## Export to Word
    generate_word_doc(overview_text, contributors_text, changes_text, revision_text)

    ## Export to HTML
    html_string = generate_html_report(overview_text, contributors_text, changes_text, revision_text)
    
    return html_string

if __name__ == "__main__":
    main()