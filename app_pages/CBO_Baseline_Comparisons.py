# -------------------------------------------------------------
# This page allows comparison of CBO baselines 
# -------------------------------------------------------------

# Imports 
import streamlit as st
from workhorses.comparing_baselines import get_mega_baseline_dataframe, compare_current_baseline_to_previous, get_baseline_data

# Load the data
cbo_csv_url = "https://github.com/US-CBO/eval-projections/blob/main/input_data/baselines.csv"
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

# User input for component, category, and subcategory
component = st.selectbox("Select a component", components)
category = st.selectbox("Select a category", categories)
subcategory = st.selectbox("Select a subcategory", subcategories)
projected_yr = st.selectbox("Select a year", projected_years)
ten_year_sum = st.checkbox("Sum over 10 years")

# Get the comparison
current_val, prior_val = compare_current_baseline_to_previous(current_baseline, prior_baseline, 
                                                              component, category, subcategory, 
                                                              projected_yr, ten_year_sum=ten_year_sum) 

# Display the comparison
st.title("CBO Baseline Comparisons")
st.write(f"Current Value: {current_val}")
st.write(f"Prior Value: {prior_val}")
st.write(f"Difference: {current_val - prior_val:,.0f}")
st.write(f"Percent Change: {((current_val - prior_val) / prior_val) * 100:.1f}%")