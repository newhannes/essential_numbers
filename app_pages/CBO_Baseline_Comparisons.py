# -------------------------------------------------------------
# This page allows comparison of CBO baselines 
# -------------------------------------------------------------

# Imports 
import streamlit as st
from workhorses.comparing_baselines import get_mega_baseline_dataframe, compare_current_baseline_to_previous, get_baseline_data

# Streamlit Title
# -----------------
st.title("CBO Baseline Comparisons")
st.write("Values are in billions of dollars.")

# Preparation
# -----------------

# Load the data
cbo_csv_url = "https://raw.githubusercontent.com/US-CBO/eval-projections/refs/heads/main/input_data/baselines.csv"
baselines = get_mega_baseline_dataframe(cbo_csv_url)

# Current and Prior Baselines
unique_baselines = baselines.index.unique().sort_values()
unique_baselines_names = [baseline.strftime("%B %Y") for baseline in unique_baselines]

first_baseline = st.selectbox("Select a baseline", unique_baselines_names)
second_baseline = st.selectbox("Select another baseline", unique_baselines_names)

current_baseline = baselines[baselines.baseline_name == first_baseline]
prior_baseline = baselines[baselines.baseline_name == second_baseline]
# current_baseline = baselines.loc[unique_baselines[-1]]
# prior_baseline = baselines.loc[unique_baselines[-2]]


components = current_baseline.component.unique()

current_baseline_date = current_baseline.baseline_name.unique()[0]
prior_baseline_date = prior_baseline.baseline_name.unique()[0]

# Streamlit Page
# -------------------


# User input for component, category, subcategory, and projected year
component = st.selectbox("Select a component", components)

if component:
    filtered_baseline = current_baseline[current_baseline["component"] == component]
    categories = set(filtered_baseline["category"]) & set(prior_baseline["category"])
    category = st.selectbox("Select a category", categories)

    if category:
        filtered_baseline = filtered_baseline[filtered_baseline["category"] == category]
        subcategories = filtered_baseline["subcategory"].unique()
        subcategory = st.selectbox("Select a subcategory", subcategories)

        if subcategory:
            projected_years = sorted(set(current_baseline["projected_fiscal_year"]) & set(prior_baseline["projected_fiscal_year"]))
            projected_yr = st.selectbox("Select a year", projected_years)

ten_year_sum = st.checkbox("Sum over 10 years (ignores year selection)")

# Get the comparison
current_val, prior_val = compare_current_baseline_to_previous(current_baseline, prior_baseline, 
                                                              component, category, subcategory, 
                                                              projected_yr, ten_year_sum=ten_year_sum) 

# Display the comparison
st.markdown(f"{current_baseline_date}: **${current_val:,.0f}**")
st.markdown(f"{prior_baseline_date}: **${prior_val:,.0f}**")
st.markdown(f"Difference: **{current_val - prior_val:,.0f}**")
st.markdown(f"Percent Change: **{((current_val - prior_val) / prior_val) * 100:.1f}%**")

# Option to view the data
if st.button("View the data"):
    st.markdown(f"## {current_baseline_date}")
    st.write(current_baseline)
    st.markdown(f"## {prior_baseline_date}")
    st.write(prior_baseline)