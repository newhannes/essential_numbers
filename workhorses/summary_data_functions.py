## Imports and variables ##
import os
import pandas as pd
from full_fred.fred import Fred
from functools import reduce
import streamlit as st
# API Keys
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()

def get_fred_data(series_id, nickname, start_date=None, end_date=None, frequency=None, agg_method=None, units=None, to_datetime=False, to_numeric=False, to_float=False, errors="raise", yoy=False, mom=False):
    data = fred.get_series_df(series_id, observation_start=start_date, observation_end=end_date, frequency=frequency, aggregation_method=agg_method, units=units)
    data = data.drop(columns=['realtime_start', 'realtime_end']).rename(columns={'value': nickname})
    if to_datetime:
        data["date"] = pd.to_datetime(data['date'])
    if to_numeric:
        data[nickname] = pd.to_numeric(data[nickname].replace('.', float("nan")), errors=errors)
    if to_float:
        data[nickname] = data[nickname].replace('.', float('nan')).astype(float, errors=errors)
    if yoy:
        data[f"{nickname} YoY"] = round(data[nickname].pct_change(periods=12) * 100, 1)
    if mom:
        data[f"{nickname} MoM"] = round(data[nickname].pct_change() * 100, 1)
    return data

## MARK: INFLATION
def get_inflation_data():
    # Constants
    BIDEN_START_MONTH = "2021-01-01"
    BIDEN_END_MONTH = "2024-12-01"
    PANDEMIC_PEAK = "2022-06-01"
    # Helper function for percentage calculations
    def multiply_by_100_and_round(x, decimals=0):
        return round(x * 100, decimals)

    ## CPI Data
    cpi = get_fred_data("CPIAUCSL", "CPI", yoy=True, to_numeric=True)  # Seasonally adjusted
    cpi_unadj = get_fred_data("CPIAUCNS", "CPI Unadjusted", yoy=True, to_numeric=True)  # Not seasonally adjusted
    core_cpi = get_fred_data("CPILFESL", "Core CPI", yoy=True, to_numeric=True)  # Seasonally adjusted
    housing_cpi = get_fred_data("CPIHOSSL", "Housing CPI", yoy=True, to_numeric=True)  # Seasonally adjusted
    food_cpi = get_fred_data("CUSR0000SAF11", "Food CPI", yoy=True, to_numeric=True)  # Seasonally adjusted
    energy_cpi = get_fred_data("CPIENGSL", "Energy CPI", yoy=True, to_numeric=True)  # Seasonally adjusted

    ## Consumer Expenditures (Family of 4)
    exp_fam_four = get_fred_data("CXUTOTALEXPLB0506M", "Avg CE HH4", to_numeric=True)
    exp_fam_four["date"] = pd.to_datetime(exp_fam_four["date"])
    exp_fam_four["year"] = exp_fam_four["date"].dt.year
    exp_fam_four.set_index("year", inplace=True)

    ## Combine CPI data
    cpi_dfs = [cpi, cpi_unadj, core_cpi, housing_cpi, food_cpi, energy_cpi]
    combined_cpi = reduce(lambda left, right: pd.merge(left, right, on="date", how="outer"), cpi_dfs)
    combined_cpi["date"] = pd.to_datetime(combined_cpi["date"])
    combined_cpi.set_index("date", inplace=True)

    ## Biden Start/End CPI Values
    biden_start_cpi = combined_cpi.loc[BIDEN_START_MONTH]
    biden_end_cpi = combined_cpi.loc[BIDEN_END_MONTH]

    ## Expenditure Calculation (2020-2021 Average)
    kole_ce = exp_fam_four.loc[2020:2021]["Avg CE HH4"].mean()

    ## Inflation Under Biden
    biden_inflation_pct = multiply_by_100_and_round(biden_end_cpi["CPI"] / biden_start_cpi["CPI"] - 1, 1)
    kole_inc = kole_ce * (biden_inflation_pct / 100)  # Increase in annual expenditure
    monthly_kole_inc = kole_inc / 12

    ## Sector-Specific Inflation Since Biden Took Office
    food_inflation_biden_pct = multiply_by_100_and_round(biden_end_cpi["Food CPI"] / biden_start_cpi["Food CPI"] - 1)
    energy_inflation_biden_pct = multiply_by_100_and_round(biden_end_cpi["Energy CPI"] / biden_start_cpi["Energy CPI"] - 1)
    housing_inflation_biden_pct = multiply_by_100_and_round(biden_end_cpi["Housing CPI"] / biden_start_cpi["Housing CPI"] - 1)

    ## Current CPI Readings
    cpi_current_yoy = combined_cpi.iloc[-1]["CPI Unadjusted YoY"]
    core_cpi_current_yoy = combined_cpi.iloc[-1]["Core CPI YoY"]
    cpi_month_year = combined_cpi.index[-1].strftime("%B %Y")

    # Pandemic Peak
    cpi_peak = combined_cpi.loc[PANDEMIC_PEAK]["CPI Unadjusted YoY"]

    ## Return Data
    return {
        "cpi_df": cpi,
        "kole_inc": round(kole_inc),
        "mon_kole_inc": round(monthly_kole_inc),
        "biden_inflation": biden_inflation_pct,
        "food_biden": int(food_inflation_biden_pct),
        "energy_biden": int(energy_inflation_biden_pct),
        "housing_biden": int(housing_inflation_biden_pct),
        "cpi_current": cpi_current_yoy,
        "core_cpi_current": core_cpi_current_yoy,
        "cpi_month_year": cpi_month_year,
        "cpi_pandemic_peak": cpi_peak,
    }

## MARK: LABOR MARKET
def get_labor_data(cpi_df):
    ## Unemployment Rate
    unemployment = get_fred_data("UNRATE", "Unemployment Rate", to_numeric=True)
    unemployment = unemployment["Unemployment Rate"].iloc[-1]

    ## Job Openings
    job_openings = get_fred_data("JTSJOL", "Job Openings", to_numeric=True)
    job_openings = job_openings["Job Openings"].iloc[-1]

    ## Real Earnings
    earnings = (
        get_fred_data("CES0500000011", "Earnings", to_numeric=True, yoy=False)
        .merge(cpi_df, on="date", how="left")
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .query("date <= '2024-12-01'")
        .dropna()
    )

    # Adjust Earnings for Inflation
    earnings["YoY Increase"] = earnings["Earnings"].diff(periods=12)
    earnings["CPI Multiplier"] = earnings["CPI"].iloc[-1] / earnings["CPI"]
    earnings["Real Earnings Today"] = (earnings["Earnings"] * earnings["CPI Multiplier"]).round(2)

    # Real Earnings Change Under Biden
    biden_real_earn = earnings.loc[earnings["date"] == "2021-01-01", "Real Earnings Today"].values[0]
    current_real_earn = earnings["Real Earnings Today"].iloc[-1]
    real_earnings_change_pct = round(((current_real_earn / biden_real_earn) - 1) * 100, 1)

    ## Labor Force Participation Rate (LFPR)
    start_date = "1974-01-01"
    labor_level = get_fred_data("CLF16OV", "Labor Force Level", start_date=start_date, to_numeric=True)
    labor_level_latest = labor_level["Labor Force Level"].iloc[-1]

    lfpr = get_fred_data("CIVPART", "LFPR", start_date=start_date, to_numeric=True, to_datetime=True).set_index("date")
    current_lfpr = lfpr["LFPR"].iloc[-1]
    current_lfpr_date = lfpr.index[-1].strftime("%B %Y")

    pre_covid_lfpr = lfpr.loc["2020-02-01", "LFPR"]
    lfpr_change = current_lfpr - pre_covid_lfpr

    # Lowest LFPR before the pandemic 
    pre_covid_lfpr_df = lfpr.loc[:'2020-01-31']
    lowest_before_pandemic = pre_covid_lfpr_df[pre_covid_lfpr_df["LFPR"] <= current_lfpr].iloc[-1]
    lowest_before_pandemic_val = lowest_before_pandemic["LFPR"]
    lowest_before_pandemic_date = lowest_before_pandemic.name.strftime("%B %Y")

    # Friendly comparison message if values are identical
    if lowest_before_pandemic_val == current_lfpr:
        lowest_before_pandemic_val = f"also {lowest_before_pandemic_val:.1f}%"
    else:
        lowest_before_pandemic_val = f"{lowest_before_pandemic_val:.1f}%"

    ## Adjusted Population Estimate (impact of LFPR change)
    pop = get_fred_data("CNP16OV", "Population", start_date=start_date, to_numeric=True, to_datetime=True).set_index("date")
    pre_covid_pop = pop.loc["2020-02-01"].values[0]

    # This calculation assumes a negative lfpr_change reduces labor force
    adjusted_pop = round((abs(lfpr_change) / 100 * pre_covid_pop) / 1_000, 1)

    ## Return
    return {
        "unemployment": unemployment,
        "job_openings": job_openings,
        "real_earnings_change_biden_pct": abs(real_earnings_change_pct),
        "current_lfpr": round(current_lfpr, 1),
        "current_lfpr_date": current_lfpr_date,
        "lowest_before_pandemic_val": lowest_before_pandemic_val,
        "lowest_before_pandemic_date": lowest_before_pandemic_date,
        "lfpr_change": round(lfpr_change, 1),
        "adjusted_pop": adjusted_pop,
        "labor_level_millions": round(labor_level_latest / 1_000)
    }

## MARK: INTEREST RATES
def get_interest_data():
    
    # Constants
    BIDEN_START_DATE = "2021-01-20"
    BIDEN_END_DATE = "2025-01-20"

    ## 10yr Treasury Yield (Daily)
    treasury_10 = get_fred_data("DGS10", "10yr Treasury Yield", to_float=True).dropna()
    treasury_10_now = treasury_10["10yr Treasury Yield"].iloc[-1].round(1)

    # Start of Biden term (Jan 2021 average)
    treasury_10_biden_start = treasury_10.loc[
        treasury_10["date"].str.startswith("2021-01"), "10yr Treasury Yield"
    ].mean().round(1)

    # End of Biden term (Dec 2024 average)
    treasury_10_biden_end = treasury_10.loc[
        treasury_10["date"].str.startswith("2024-12"), "10yr Treasury Yield"
    ].mean().round(1)

    ## Federal Funds Target Rate (Lower & Upper)
    fed_target_data = {
        "lower": get_fred_data("DFEDTARL", "Fed Funds Target Lower", to_numeric=True, to_datetime=True),
        "upper": get_fred_data("DFEDTARU", "Fed Funds Target Upper", to_numeric=True, to_datetime=True),
    }

    fed_target_results = {}

    for key, df in fed_target_data.items():
        # Latest value
        fed_target_results[f"{key}_now"] = df.iloc[-1]["Fed Funds Target " + key.capitalize()]

        # Biden Start (first rate after or on start date)
        fed_target_results[f"{key}_biden_start"] = df.loc[df["date"] >= BIDEN_START_DATE, "Fed Funds Target " + key.capitalize()].iloc[0]

        # Biden End (last rate before or on end date)
        fed_target_results[f"{key}_biden_end"] = df.loc[df["date"] <= BIDEN_END_DATE, "Fed Funds Target " + key.capitalize()].iloc[-1]

    ## Return Data
    dict = {
        "treasury_10_now": treasury_10_now,
        "treasury_10_biden_start": treasury_10_biden_start,
        "treasury_10_biden_end": treasury_10_biden_end,
        "fed_target_lower_now": fed_target_results["lower_now"],
        "fed_target_upper_now": fed_target_results["upper_now"],
        "fed_target_lower_biden_start": fed_target_results["lower_biden_start"],
        "fed_target_upper_biden_start": fed_target_results["upper_biden_start"],
        "fed_target_lower_biden_end": fed_target_results["lower_biden_end"],
        "fed_target_upper_biden_end": fed_target_results["upper_biden_end"],
    }

    return dict

## MARK: GAS AND OIL
def get_gas_oil_data():
    
    def calculate_averages(data, price_col, start_trump, end_trump, start_biden, end_biden):
        trump_avg = data[start_trump:end_trump][price_col].dropna().mean()
        biden_avg = data[start_biden:end_biden][price_col].dropna().mean()
        latest_price = data[price_col].dropna().iloc[-1]

        # Format with 2 decimal places
        return (
            f"{trump_avg:.2f}",
            f"{biden_avg:.2f}",
            f"{latest_price:.2f}"
        )

    # Constants
    START_TRUMP = "2017-01-20"
    END_TRUMP = "2021-01-19"
    START_BIDEN = "2021-01-20"
    END_BIDEN = "2025-01-19"

    # Gas Data (Weekly)
    gas = get_fred_data("GASREGW", "gas_price", to_numeric=True).set_index("date")
    gas_trump_avg, gas_biden_avg, gas_now = calculate_averages(
        gas, "gas_price", START_TRUMP, END_TRUMP, START_BIDEN, END_BIDEN
    )

    # Oil Data (Daily)
    oil = get_fred_data("DCOILWTICO", "oil_price", to_numeric=True).set_index("date")
    oil_trump_avg, oil_biden_avg, oil_now = calculate_averages(
        oil, "oil_price", START_TRUMP, END_TRUMP, START_BIDEN, END_BIDEN
    )

    # Return Data
    dict = {
        "gas_trump_average": gas_trump_avg,
        "gas_biden_average": gas_biden_avg,
        "gas_now": gas_now,
        "oil_trump_average": oil_trump_avg,
        "oil_biden_average": oil_biden_avg,
        "oil_now": oil_now,
    }

    return dict

print("Summary stats helper functions retrieved.")