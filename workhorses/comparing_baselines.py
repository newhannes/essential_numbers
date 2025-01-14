# -------------------------------------------------
# Stores helper functions for comparing baselines
# -------------------------------------------------

# Imports
import pandas as pd

# Load the data
def get_mega_baseline_dataframe(url):

    cbo_baseline = (
        pd.read_csv(url)
        .drop(columns=["Spring_flag", "Winter_flag"])
        .assign(
            baseline_date = lambda x: pd.to_datetime(x["baseline_date"], format="%Y-%m-%d"),
            baseline_name = lambda x: x["baseline_date"].str.strftime("%B %Y")
            )
        .set_index("baseline_date")
    )

    return cbo_baseline

def compare_current_baseline_to_previous(current_baseline, previous_baseline,
                                         component, category, subcategory,
                                         projected_yr=2024, ten_year_sum=False):
    
    query = f"component == '{component}' and category == '{category}' and subcategory == '{subcategory}' and projected_fiscal_year == {projected_yr}"
    
    if ten_year_sum:
        query = query.replace(f"and projected_fiscal_year == {projected_yr}", "and projected_year_number > 1")
        projected_yr = "10yr"
    
    current_val = current_baseline.query(query)['value'].values[0] if not sum else current_baseline.query(query)['value'].sum()
    prior_val = previous_baseline.query(query)['value'].values[0] if not sum else previous_baseline.query(query)['value'].sum()

    return current_val, prior_val

def get_baseline_data(baseline_date, baselines, 
                      component=None, category=None, 
                      subcategory=None, projected_fiscal_year=None):
    
    baseline = baselines[baselines.baseline_name == baseline_date]
    
    conditions = []
    arguments = ["component", "category", "subcategory", "projected_fiscal_year"]
    params = [component, category, subcategory, projected_fiscal_year]
    
    for param, argument in zip(params, arguments):
        if param is not None:
            if isinstance(param, str):
                conditions.append(f"{argument} == '{param}'")
            else:
                conditions.append(f"{argument} == {param}")
    
    query = " and ".join(conditions) if conditions else "True"
    return baseline.query(query)



