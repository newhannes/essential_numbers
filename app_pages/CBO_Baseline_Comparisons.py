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
components = current_baseline.component.unique()
current_baseline_date = current_baseline.baseline_name.unique()[0]
prior_baseline_date = prior_baseline.baseline_name.unique()[0]

# Streamlit Page
# -------------------
st.title("CBO Baseline Comparisons")

# User input for component, category, subcategory, and projected year
component = st.selectbox("Select a component", components)

if component:
    filtered_baseline = current_baseline[current_baseline["component"] == component]
    categories = filtered_baseline["category"].unique()
    category = st.selectbox("Select a category", categories)

    if category:
        filtered_baseline = filtered_baseline[filtered_baseline["category"] == category]
        subcategories = filtered_baseline["subcategory"].unique()
        subcategory = st.selectbox("Select a subcategory", subcategories)

        if subcategory:
            filtered_baseline = filtered_baseline[filtered_baseline["subcategory"] == subcategory]
            projected_years = filtered_baseline["projected_fiscal_year"].unique()
            projected_yr = st.selectbox("Select a year", projected_years)

ten_year_sum = st.checkbox("Sum over 10 years")

# Get the comparison
current_val, prior_val = compare_current_baseline_to_previous(current_baseline, prior_baseline, 
                                                              component, category, subcategory, 
                                                              projected_yr, ten_year_sum=ten_year_sum) 

# Display the comparison
st.markdown(f"{current_baseline_date}: **${current_val:,.0f}**")
st.markdown(f"{prior_baseline_date}: **${prior_val:,.0f}**")
st.markdown(f"Difference: **{current_val - prior_val:,.0f}**")
st.markdown(f"Percent Change: **{((current_val - prior_val) / prior_val) * 100:.1f}%**")