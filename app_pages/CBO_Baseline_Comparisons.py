# -------------------------------------------------------------
# This page allows comparison of CBO baselines 
# -------------------------------------------------------------

# Imports 
import streamlit as st
from workhorses.comparing_baselines import get_mega_baseline_dataframe, compare_current_baseline_to_previous, get_baseline_data

# Preparation
# -----------------

# Load the data
cbo_csv_url = "https://raw.githubusercontent.com/US-CBO/eval-projections/refs/heads/main/input_data/baselines.csv"
baselines = get_mega_baseline_dataframe(cbo_csv_url)

# Current and Prior Baselines
unique_baselines = baselines.index.unique().sort_values()
current_baseline = baselines.loc[unique_baselines[-1]]
prior_baseline = baselines.loc[unique_baselines[-2]]

# Options for component, category, and subcategory
components = current_baseline.component.unique()
categories = current_baseline.category.unique()
subcategories = current_baseline.subcategory.unique()
projected_years = current_baseline.projected_fiscal_year.unique()


# Streamlit Page
# -------------------
st.title("CBO Baseline Comparisons")

# User input for component, category, and subcategory
component = st.selectbox("Select a component", components)

if component:
    category = st.selectbox("Select a category", current_baseline.query(f"component == '{component}'").category.unique())
if category:
    subcategory = st.selectbox("Select a subcategory", current_baseline.query(f"component == '{component}' and category == '{category}'").subcategory.unique())
if subcategory:
    projected_yr = st.selectbox("Select a year", current_baseline.query(f"component == '{component}' and category == '{category}' and subcategory == '{subcategory}'").projected_fiscal_year.unique())

# subcategory = st.selectbox("Select a subcategory", subcategories)
# projected_yr = st.selectbox("Select a year", projected_years)
ten_year_sum = st.checkbox("Sum over 10 years")

# Get the comparison
current_val, prior_val = compare_current_baseline_to_previous(current_baseline, prior_baseline, 
                                                              component, category, subcategory, 
                                                              projected_yr, ten_year_sum=ten_year_sum) 

# Display the comparison
st.write(f"Current Value: ${current_val:,.0f}")
st.write(f"Prior Value: {prior_val:,.0f}")
st.write(f"Difference: {current_val - prior_val:,.0f}")
st.write(f"Percent Change: {((current_val - prior_val) / prior_val) * 100:.1f}%")