
import pandas as pd
import requests
import time
import beaapi
import re
import numpy as np

dark_grey_3 = "#3C3C3C"
rose_red = "#B03A2E"


## Contributor Helper Functions
def get_contributor_by_rank(contributors, rank):
    """
    Get the contributor by rank.
    
    Parameters:
    contributors (DataFrame): DataFrame containing the contributors data.
    rank (int): Rank of the contributor (1 = largest contributor, 2 = second largest, etc.).
    
    Returns:
    Series: The contributor series corresponding to the given rank.
    """
    sorted_contributors = contributors.sort_values(by="share_of_growth", ascending=False)
    return sorted_contributors.iloc[rank - 1]

def get_contributor_dataframe(contributors_expanded_df, contributor_name, main_contributors_line_number_dict):
    """
    Get the largest explainer within a contributor.
    
    Parameters:
    contributors_expanded_df (DataFrame): DataFrame containing the current quarter's contributors data.
    contributor_name: Name of contibutor (nickname).
    
    Returns:
    Dataframe: dataframe with the underlying data for a given main contributor.
    """
   
    contributor_linenumber = main_contributors_line_number_dict[contributor_name]
    # Find the next contributor in the main contributors list
    next_contributor = next((key for key, value in main_contributors_line_number_dict.items() if value > contributor_linenumber), None)
    
    # Filter the DataFrame to get the largest contributor's data
    if next_contributor:
        contributor_df = contributors_expanded_df[(contributors_expanded_df["LineNumber"] >= contributor_linenumber) & 
                                                        (contributors_expanded_df["LineNumber"] < main_contributors_line_number_dict[next_contributor])]
    else:
        contributor_df = contributors_expanded_df[contributors_expanded_df["LineNumber"] >= contributor_linenumber]
    
    return contributor_df

def get_qualifier(contributor, explainer):
    """
    Get the qualifier for the largest explainer.
    
    Parameters:
    contributor (series): Series of the contributor.
    largest_explainer (Series): Series containing the largest explainer data.
    
    Returns:
    str: The qualifier for the largest explainer.
    """
    if contributor.NAME == "Private investment":
        qualifier = "investment" if "investment" not in explainer.NAME else ""
    if contributor.NAME in ["Exports", "Imports"]:
        qualifier = contributor.NAME.lower()
    if contributor.NAME in ["Consumer spending", "Government spending and investment"]:
        qualifier = "spending"
    return qualifier

def format_list_with_and(items):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"

def generate_private_investment_decorator(contributors_expanded_df, main_contributors_line_number_dict):
    
    private_investment_contibutor = get_contributor_dataframe(contributors_expanded_df, "Private investment", main_contributors_line_number_dict)
    private_investment_val = private_investment_contibutor["DataValue"].values[0]
    private_investment_subcats = private_investment_contibutor[private_investment_contibutor.NAME.isin(["Structures", "Equipment", "Intellectual property products", "Residential", "Change in private inventories"])]
    private_investment_subcats.loc[private_investment_subcats["NAME"] == "Change in private inventories", "NAME"] = "Inventory"
    
    positive_private_investment = private_investment_subcats.query('DataValue > 0')
    negative_private_investment = private_investment_subcats.query('DataValue < 0')
    positive_private_investment_names = [name.lower() for name in positive_private_investment["NAME"].tolist()]
    negative_private_investment_names = [name.lower() for name in negative_private_investment["NAME"].tolist()]
    
    if private_investment_val > 0:
        investment_decorator = f" Growth attributable to {format_list_with_and(positive_private_investment_names)} investment was partially offset by contractions in {format_list_with_and(negative_private_investment_names)} investment."
    if private_investment_val < 0:
        investment_decorator = f" Declines in {format_list_with_and(negative_private_investment_names)} investment were partially offset by growth in {format_list_with_and(positive_private_investment_names)} investment."
    return investment_decorator

## Component Helper Functions 
def get_component_df(component_name, current_pct_change, pct_change_linenumber_dict):
    """
    Get the DataFrame for a given component.
    
    Parameters:
    component_name (str): Name of the component.
    current_pct_change (DataFrame): DataFrame containing the current quarter's percent change data.
    
    Returns:
    DataFrame: DataFrame containing the data for the given component.
    """
    component_linenumber = pct_change_linenumber_dict[component_name]
    next_linenum = next((value for key, value in pct_change_linenumber_dict.items() if value > component_linenumber), 1e3)
    component_df = current_pct_change.loc[(current_pct_change.LineNumber >= component_linenumber) & (current_pct_change.LineNumber < next_linenum)]
    return component_df

def increase_or_decrease_text(val, tense="past"):
    """
    Get the increase or decrease text.
    
    Parameters:
    val (float): Value to determine if it increased or decreased.
    tense (str): Tense of the text ("past" or "future").
    
    Returns:
    str: The increase or decrease text.
    """
    if val > 0:
        return "increased" if tense == "past" else "increasing"
    if val < 0:
        return "decreased" if tense == "past" else "decreasing"
    return "remained unchanged"

def generate_change_text(component_df):
    """
    Generate the change text for a given component.
    
    Parameters:
    component_df (DataFrame): DataFrame containing the data for the component.
    
    Returns:
    str: The change text for the component.
    """
    component_name = component_df["LineDescription"].iloc[0]
    component_val = component_df["DataValue"].iloc[0]
    component_subcats = component_df[component_df.LineDescription != component_name]
    positive_subcats = component_subcats.query('DataValue > 0')
    positive_subcat_names = [name.lower() for name in positive_subcats["LineDescription"].tolist()]
    negative_subcats = component_subcats.query('DataValue < 0')
    negative_subcat_names = [name.lower() for name in negative_subcats["LineDescription"].tolist()]
    if component_val > 0:
            intro = f"{component_name} grew by {component_val:.1f} percent,"            
    if component_val < 0:
            intro = f"{component_name} declined by {component_val:.1f} percent,"
    
    if component_name in ["Exports", "Imports"]:
        goods_val = component_df.query('LineDescription == "Goods"')["DataValue"].values[0]
        services_val = component_df.query('LineDescription == "Services"')["DataValue"].values[0]
        change_text = f"{intro} with goods {component_name.lower()} {increase_or_decrease_text(goods_val, tense='ing')} by {goods_val:.1f} percent and services {component_name.lower()} {increase_or_decrease_text(services_val, tense='ing')} by {services_val:.1f} percent."
            
    if component_name == "Personal consumption expenditures":
        goods_val = component_df.query('LineDescription == "Goods"')["DataValue"].values[0]
        services_val = component_df.query('LineDescription == "Services"')["DataValue"].values[0]
        change_text = f"{intro} with spending on goods {increase_or_decrease_text(goods_val, tense='ing')} by {goods_val:.1f} percent and spending on services {increase_or_decrease_text(services_val, tense='ing')} by {services_val:.1f} percent."

    if component_name == "Gross private domestic investment":
       
        positive_subcat_names = [subcat for subcat in positive_subcat_names if subcat not in ["fixed investment", "nonresidential"]]
        negative_subcat_names = [subcat for subcat in negative_subcat_names if subcat not in ["fixed investment", "nonresidential"]]
        positive_subcat_names = [subcat if subcat != "structures" else "nonresidential structures" for subcat in positive_subcat_names]
        negative_subcat_names = [subcat if subcat != "structures" else "nonresidential structures" for subcat in negative_subcat_names]
        
        if component_val > 0:
            change_text = f'{intro} with growth in {format_list_with_and(positive_subcat_names)} investment partially offset by declines in {format_list_with_and(negative_subcat_names)} investment.'
        if component_val < 0:
            change_text = f'{intro} with declines in {format_list_with_and(negative_subcat_names)} investment partially offset by growth in {format_list_with_and(positive_subcat_names)} investment.'
    
    if component_name == "Government consumption expenditures and gross investment":
        if component_val > 0:
            if len(negative_subcat_names) == 0:
                change_text = f"{intro} with growth in federal defense and nondefense spending as well as in state and local spending."
            else:
                change_text = f"{intro} with growth in {format_list_with_and(positive_subcat_names)} spending partially offset by declines in {format_list_with_and(negative_subcat_names)} spending."
        if component_val < 0:
            change_text = f"{intro} with declines in {format_list_with_and(negative_subcat_names)} spending partially offset by growth in {format_list_with_and(positive_subcat_names)} spending."

    return change_text


## Revision Helper Functions
def extract_numbers(text):
    # Regular expression to match up to three numbers at the end of the string
    match = re.findall(r'(-?\d+\.\d+)', text)
    
    # Ensure the list has exactly 3 numbers; fill with "N/A" if necessary
    numbers = match[-3:]  # Take the last three numbers, if available
    while len(numbers) < 3:
        numbers.append(np.nan)
    
    return numbers

def extract_variable(text):
    # Regular expression to find the words after the first number and before two or more periods
    match = re.search(r'\d+([A-Za-z0-9\s\(\)\-\,\.]+?)(?=\.+)', text)
    
    if match:
        # Return the extracted variable, stripped of leading/trailing spaces
        return re.sub(r"\d+", '', match.group(1)).strip()
    else:
        # Return N/A if no match is found
        return np.nan
    
def get_list_of_changed(type, df):
    if type not in ["unchanged", "increased", "decreased"]:
        raise ValueError("Type must be 'unchanged', 'increased', or 'decreased'")
    query = "difference == 0" if type == "unchanged" else f"difference {'>' if type == 'increased' else '<'} 0"
    return df.query(query)["variable"].to_list()

def draw_row(ax, data, row, name_x, original_x, revised_x, difference_x, num_kws):
    if data[0] in ["Nonresidential investment", "Residential investment", "Federal", "State and local"]:
        name_x = 0.25
    ax.text(name_x, row, data[0], ha='left', va='center', fontsize=12, color=dark_grey_3)
    ax.text(original_x, row, f"{data[1]:.1f}", **num_kws)
    ax.text(revised_x, row, f"{data[2]:.1f}", **num_kws)
    color = "green" if data[3] > 0 else rose_red if data[3] < 0 else "black"
    num_kws["color"] = color
    num_kws["fontweight"] = "bold"
    ax.text(difference_x, row, f"{data[3]:.1f}", **num_kws)