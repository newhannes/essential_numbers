############# =============== PROCESS GDP RELEASE DATA =============== #############

import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
import PyPDF2 as p2
from io import BytesIO
from workhorses.gdp_report.autoreport_helpers import * # test

## MARK: Overview
def scrape_release_info():
    ## Scrape the current GDP release title/type from website
    url = "https://www.bea.gov/data/gdp/gross-domestic-product"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    release_title = soup.find(class_="field field--name-field-subtitle field--type-string field--label-hidden field--item").text
    release_stage = release_title[release_title.find("(")+1:release_title.find(")")]
    current_q_text = release_title[release_title.find(",")+2:release_title.find("2")-1]
    return release_stage, current_q_text

def generate_overview_text(pct_change_raw, gdp_raw, debt_df, current_quarter, prior_quarter, release_stage, current_q_text):
    
    current_q = current_quarter
    prior_q = prior_quarter
    
    real_gdp = pct_change_raw.query('LineDescription == "Gross domestic product" and TimePeriod == @current_q')["DataValue"].values[0]
    real_gdp_last = pct_change_raw.query('LineDescription == "Gross domestic product" and TimePeriod == @prior_q')["DataValue"].values[0] # type: ignore
    gdp_nominal = gdp_raw.query('LineDescription == "Gross domestic product" and TimePeriod == @current_q')["DataValue"].values[0] 
    
    fifty_yr_avg = (
        pct_change_raw
        .loc[(pct_change_raw.LineDescription == "Gross domestic product") & (pct_change_raw.TimePeriod >= str(int(current_q[:4])-50) + current_q[-2:]), "DataValue"]
        .mean()
        .round(1)
    )

    difference_from_avg = round(real_gdp - fifty_yr_avg, 1)
    above_or_below = "above" if difference_from_avg > 0 else "below" if difference_from_avg < 0 else None
    difference_from_avg_text = f"{above_or_below} the 50 year average" if difference_from_avg != 0 else "equal to the 50 year average"

    ## Debt-to-GDP ratio
    current_debt_millions = debt_df['tot_pub_debt_out_amt'].iloc[-1] / 1e6
    debt_to_gdp = current_debt_millions / gdp_nominal

    ## Sentence 
    OVERVIEW_TEXT = f"""
    Real GDP grew at an annual rate of {real_gdp} percent in the {current_q_text.lower()} of {current_q[:4]}, according to the Bureau of Economic Analysis's {release_stage.lower()}, {difference_from_avg_text}.
    Growth last quarter was {real_gdp_last} percent. GDP now amounts to ${gdp_nominal/1e6:.1f} trillion in current dollars. With the gross national debt currently at ${current_debt_millions/1e6:.1f} trillion, this debt-to-GDP ratio is {debt_to_gdp:.0%}."""

    OVERVIEW_TEXT = OVERVIEW_TEXT.replace("\n", " ")
    return OVERVIEW_TEXT

## MARK: Composition of GDP
def clean_contributors_data(contributors_raw, current_quarter):
    main_contributors = [
    "Personal consumption expenditures", 
    "Gross private domestic investment", 
    "Net exports of goods and services", 
    "Exports", "Imports", 
    "Government consumption expenditures and gross investment"
    ]

    rename_dict = {
    "Personal consumption expenditures": "Consumer spending",
    "Gross private domestic investment": "Private investment",
    "Net exports of goods and services": "Net exports",
    "Exports": "Exports",
    "Imports": "Imports",
    "Government consumption expenditures and gross investment": "Government spending and investment",
    }

    main_contributors_df = (
        contributors_raw
        .query('LineDescription in @main_contributors')
        .query('TimePeriod == @current_quarter')
        .loc[:, ["LineDescription", "LineNumber", "TimePeriod", "CL_UNIT", "DataValue"]]
        .rename(columns={"LineDescription": "NAME"})
        .assign(
            sign = lambda x: np.where(x["DataValue"] > 0, "positive", "negative"),
            NAME = lambda x: x["NAME"].map(rename_dict)
                )
    )

    contributors_expanded_df = (
        contributors_raw
        .query('TimePeriod == @current_quarter')
        .loc[:, ["LineDescription", "LineNumber", "TimePeriod", "CL_UNIT", "DataValue"]]
        .rename(columns={"LineDescription": "NAME"})
    ) 

    main_contributors_line_number_dict = dict(zip(main_contributors_df["NAME"], main_contributors_df["LineNumber"]))
    contributors_chart_data = main_contributors_df.query('NAME != "Exports" and NAME != "Imports"')

    main_contributors_df = (
        main_contributors_df
        .query('NAME != "Net exports"')
        .assign(share_of_growth = lambda x: round(x["DataValue"] / x["DataValue"].sum() * 100))
    )

    return main_contributors_df, contributors_expanded_df, contributors_chart_data, main_contributors_line_number_dict


def generate_contributors_text(main_contributors_df, contributors_expanded_df, main_contributors_line_number_dict, real_gdp):
    
    contributors = [
        get_contributor_by_rank(main_contributors_df, rank)
        for rank in range(1, 6)
    ]

    contributor_dfs = [
        get_contributor_dataframe(contributors_expanded_df, contributor["NAME"], main_contributors_line_number_dict)
        for contributor in contributors
    ]

    explainers = [
        df.loc[df.iloc[1:]["DataValue"].idxmax()]
        for df in contributor_dfs
    ]

    # Text generation
    CONTRIBUTOR_TEXT = f"""
    Of the {real_gdp} percent growth in real GDP, {contributors[0].NAME.lower()} was the largest contributor to growth, accounting for {contributors[0].share_of_growth:.0f} percent of net growth.
    Within {contributors[0].NAME.lower()}, {explainers[0].NAME.lower()} {get_qualifier(contributors[0], explainers[0])} was the largest contributor and made up {explainers[0].DataValue / real_gdp * 100:.0f} percent of growth.
    The second largest contributor was {contributors[1].NAME.lower()} which accounted for {contributors[1].share_of_growth:.0f} percent of total growth, with {explainers[1].NAME.lower()} {get_qualifier(contributors[1], explainers[1])} 
    driving the contribution of {contributors[1].NAME.lower()}. 
    {contributors[2].NAME} accounted for {contributors[2].share_of_growth:.0f} percent of total growth, with this growth primarily attributable to {explainers[3].NAME.lower()} {get_qualifier(contributors[2], explainers[3])}.
    {contributors[3].NAME} comprised {contributors[3].share_of_growth:.0f} percent of total growth. 
    {contributors[4].NAME} accounted for {contributors[4].share_of_growth:.0f} percent of total growth.
    """

    # Import decorator
    import_decorator = ", which are counted against GDP,"
    imports_index = CONTRIBUTOR_TEXT.lower().find("imports") + len("imports")
    CONTRIBUTOR_TEXT = CONTRIBUTOR_TEXT[:imports_index] + import_decorator + CONTRIBUTOR_TEXT[imports_index:]

    # Investment decorator
    investment_decorator = generate_private_investment_decorator(contributors_expanded_df, main_contributors_line_number_dict)
    investment_index = CONTRIBUTOR_TEXT.lower().find("private investment")
    first_period_index = CONTRIBUTOR_TEXT.find(".", investment_index)
    CONTRIBUTOR_TEXT = CONTRIBUTOR_TEXT[:first_period_index + 1] + investment_decorator + CONTRIBUTOR_TEXT[first_period_index + 1:]

    # Final text
    CONTRIBUTOR_TEXT = CONTRIBUTOR_TEXT.replace("\n", " ")
    return CONTRIBUTOR_TEXT


## MARK: Changes This Quarter
def generate_changes_text(pct_change_raw, current_quarter):
    
    ## Data prep
    current_pct_change = (
        pct_change_raw.query('TimePeriod == @current_quarter')
        .drop(columns=["TableName", "TimePeriod", "CL_UNIT", "UNIT_MULT", "METRIC_NAME", "NoteRef"])
        .iloc[1:-1] # remove the first and last rows (current and real GDP)
    )

    pct_change_linenumber_dict = {
        'Personal consumption expenditures': 2,
        'Gross private domestic investment': 7,
        'Exports': 16,
        'Imports': 19,
        'Government consumption expenditures and gross investment': 22
    }

    # Get the DataFrames for the main components
    consumer_spending_pctchange_df = get_component_df("Personal consumption expenditures", current_pct_change, pct_change_linenumber_dict)
    investment_pctchange_df = get_component_df("Gross private domestic investment", current_pct_change, pct_change_linenumber_dict)
    exports_pctchange_df = get_component_df("Exports", current_pct_change, pct_change_linenumber_dict)
    imports_pctchange_df = get_component_df("Imports", current_pct_change, pct_change_linenumber_dict)
    gov_pctchange_df = get_component_df("Government consumption expenditures and gross investment", current_pct_change, pct_change_linenumber_dict)
    
    # Generate the change text for each component
    consumer_spending_change_text = generate_change_text(consumer_spending_pctchange_df)
    investment_change_text = generate_change_text(investment_pctchange_df)
    exports_change_text = generate_change_text(exports_pctchange_df)
    imports_change_text = generate_change_text(imports_pctchange_df)
    gov_change_text = generate_change_text(gov_pctchange_df)

    ## Text
    CHANGES_TEXT = f"""
    {consumer_spending_change_text.replace("Personal consumption expenditures", "Consumer spending")}
    {investment_change_text.replace("Gross private domestic investment", "Private investment")}
    {gov_change_text.replace("Government consumption expenditures and gross investment", "Government spending and investment")}
    {exports_change_text}
    {imports_change_text}
    """
    CHANGES_TEXT = CHANGES_TEXT.replace("\n", " ")
    return CHANGES_TEXT


## MARK: Revisions
def clean_revisions_data(data):
    
    revision_pct_change = (
            pd.DataFrame(data, columns=["Extracted Text"])
            .assign(
                variable=lambda df: df["Extracted Text"].apply(extract_variable),
                temp=lambda df: df["Extracted Text"].apply(extract_numbers).tolist()
            )
            .assign(
                original=lambda df: [x[0] for x in df["temp"]],
                revised=lambda df: [x[1] for x in df["temp"]],
                difference=lambda df: [x[2] for x in df["temp"]]
            )
            .drop(columns=["temp"])
            .astype({"original": float, "revised": float, "difference": float})
            .loc[:, ["variable", "original", "revised", "difference", "Extracted Text"]]
        )

    # Remove everything after addenda except for disposable personal income. Then select all rows up to the first instance of disposable personal income. 
    addenda_index = revision_pct_change[revision_pct_change["Extracted Text"].str.contains("Addenda", na=False)].index[0]
    disposable_index = revision_pct_change[revision_pct_change["variable"].str.contains("Disposable personal income", na=False)].index[0]

    revision_pct_change = (
        revision_pct_change
        .query(
            "(index < @addenda_index) or "
            "(variable.str.contains('Disposable personal income', na=False) and index <= @disposable_index)"
        )
        .dropna()
    )

    revision_variables = ["Gross domestic product (GDP)", "Personal consumption expenditures (PCE)", 
                        "Gross private domestic investment", "Nonresidential", "Residential", 
                        "Exports", "Imports", 
                        "Government consumption expenditures and gross investment", "Federal", "State and local",
                        "Disposable personal income"]

    revision_rename_dict = {
        "Gross domestic product (GDP)": "Gross domestic product",
        "Personal consumption expenditures (PCE)": "Consumer spending",
        "Gross private domestic investment": "Gross private investment",
        "Nonresidential": "Nonresidential investment",
        "Residential": "Residential investment",
        "Government consumption expenditures and gross investment": "Government spending and investment",
        "Federal": "Federal government spending",
        "State and local": "State and local government spending"
    }

    revision_pct_change = (
        revision_pct_change
        .query("variable in @revision_variables")
        .assign(variable=lambda x: x["variable"].map(revision_rename_dict).fillna(x["variable"])) # rename variables, fill with original if not in dict
    )

    no_disposable = revision_pct_change.query("variable != 'Disposable personal income'")
    return no_disposable

def scrape_revisions_data(current_quarter, release_stage):
    release = "2nd" if "Second" in release_stage else "3rd"
    original = "Advance Estimate" if "Second" in release_stage else "Second Estimate"
    revision_url = f"https://apps.bea.gov/national/pdf/revision_information/rev1-{current_quarter[-1]}q{current_quarter[2:4]}-{release}.pdf"

    response = requests.get(revision_url)
    pdf_file = BytesIO(response.content)
    pdf_reader = p2.PdfReader(pdf_file)

    data = []
    for page in pdf_reader.pages:
        for content in page.extract_text().split("\n"):
            data.append(content)
    return data, original

def generate_revisions_text(no_disposable, release_stage, original):
    
    unchanged_list = get_list_of_changed("unchanged", no_disposable)
    increased_list = get_list_of_changed("increased", no_disposable)
    increased_list = format_list_with_and(increased_list) # so we can capitalize properly
    decreased_list = get_list_of_changed("decreased", no_disposable)

    unchanged_text = f"In the {release_stage.lower()}, {format_list_with_and(unchanged_list).lower()} remained unchanged from the {original.lower()}."
    changed_text = f"{increased_list[0] + increased_list[1:].lower()} were revised upwards while {format_list_with_and(decreased_list).lower()} were revised downwards."

    REVISION_TEXT = f"""
    {unchanged_text}
    {changed_text}
    These changes are in the table below. 
    """
    REVISION_TEXT = REVISION_TEXT.replace("\n", " ")
    return REVISION_TEXT