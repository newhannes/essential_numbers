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

## INFLATION ##
def get_inflation_data():
    # CPI
    cpi = get_fred_data("CPIAUCSL", "CPI", yoy=True, to_numeric=True) # seasonally adjusted
    cpi_unadj = get_fred_data("CPIAUCNS", "CPI Unadjusted", yoy=True, to_numeric=True) # not seasonally adjusted
    core_cpi = get_fred_data("CPILFESL", "Core CPI", to_numeric=True, yoy=True) # seasonally adjusted
    housing = get_fred_data("CPIHOSSL", "Housing CPI", to_numeric=True, yoy=True) # seasonally adjusted
    food = get_fred_data("CUSR0000SAF11", "Food CPI", to_numeric=True, yoy=True) # seasonally adjusted
    energy = get_fred_data("CPIENGSL", "Energy CPI", to_numeric=True, yoy=True) # seasonally adjusted
    # Consumer Expenditures
    exp_fam_four = get_fred_data("CXUTOTALEXPLB0506M", "Avg CE HH4", to_numeric=True)
    exp_fam_four["date"] = pd.to_datetime(exp_fam_four["date"])
    exp_fam_four["year"] = exp_fam_four["date"].dt.year
    exp_fam_four.set_index("year", inplace=True)
    # Merge
    list_of_dfs = [cpi, cpi_unadj, core_cpi, housing, food, energy]
    combined_cpi = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), list_of_dfs)
    combined_cpi["date"] = pd.to_datetime(combined_cpi["date"])
    combined_cpi = combined_cpi.set_index("date")
    # Calculations and Currents 
    kole_ce = exp_fam_four.loc[2020:2021]["Avg CE HH4"].mean() # this is the average of CE for 2020 and 2021. Idk why its done this way. 
    biden_inflation = round((combined_cpi.iloc[-1]["CPI"] / combined_cpi.loc["January 2021", "CPI"] - 1) * 100,1).values[0]
    kole_inc = kole_ce * (biden_inflation / 100 + 1) - kole_ce # take kole_ce and multiply by bidenflation. then subtract kole_ce to get the increase.
    mon_kole_inc = kole_inc / 12

    if pd.isna(kole_inc):
        print(f"biden_inflation: {biden_inflation}, kole_ce: {kole_ce}")

    # Food, energy, housing since Biden
    food_biden = round((combined_cpi.loc["December 2024", "Food CPI"] / combined_cpi.loc["January 2021", "Food CPI"] - 1) * 100, 0).values[0]
    energy_biden = round((combined_cpi.loc["December 2024", "Energy CPI"] / combined_cpi.loc["January 2021", "Energy CPI"] - 1) * 100, 0).values[0]
    housing_biden = round((combined_cpi.loc["December 2024", "Housing CPI"] / combined_cpi.loc["January 2021", "Housing CPI"] - 1) * 100, 0).values[0]
    # Currents
    cpi_current = combined_cpi.iloc[-1]["CPI Unadjusted YoY"]
    core_cpi_current = combined_cpi.iloc[-1]["Core CPI YoY"]
    ## Return
    return {
        "cpi_df": cpi,
        "kole_inc": round(kole_inc),
        "mon_kole_inc": round(mon_kole_inc),
        "biden_inflation": biden_inflation,
        "food_biden": int(food_biden),
        "energy_biden": int(energy_biden),
        "housing_biden": int(housing_biden),
        "cpi_current": cpi_current,
        "core_cpi_current": core_cpi_current,
        "cpi_month_year" : combined_cpi.index[-1].strftime("%B %Y")
    }

## LABOR MARKET ##
def get_labor_data(cpi_df):
    ## Unemployment
    unemployment = get_fred_data("UNRATE", "Unemployment Rate", to_numeric=True)
    unemployment = unemployment["Unemployment Rate"].iloc[-1]
    ## Job Openings
    job_openings = get_fred_data("JTSJOL", "Job Openings", to_numeric=True)
    job_openings = job_openings["Job Openings"].iloc[-1]
    ## Real Earnings
    earnings = get_fred_data("CES0500000011", "Earnings", to_numeric=True, yoy=False) # seasonally adjusted, avg weekly earnings
    earnings = earnings.merge(cpi_df, on="date", how="left")
    earnings["date"] = pd.to_datetime(earnings["date"], format="%Y-%m-%d")
    earnings = earnings.dropna() # drop missing values, this occurs when one data source is ahead of another
    earnings["YoY Increase"] = earnings["Earnings"].diff(periods=12)
    earnings["CPI Multiplier"] = earnings["CPI"].iloc[-1] / earnings["CPI"]
    earnings["Real Earnings, Today's Dollars"] = round(earnings["Earnings"] * earnings["CPI Multiplier"], 2) # take the real earnings and multiply by the CPI ratio to get the real earnings in today's dollars
    # Stats
    biden_real_earn = earnings.loc[earnings["date"] == "2021-01-01", "Real Earnings, Today's Dollars"].values[0]
    current_real_earn = earnings["Earnings"].iloc[-1]
    real_earn_change = round(((biden_real_earn/current_real_earn)-1)*100,2)
    real_earnings_biden = round(100 - ((current_real_earn / biden_real_earn) * 100), 1)
    ## Labor Force Participation Rate
    start_date = "1974-01-01"
    labor_level = get_fred_data("CLF16OV", "Labor Force Level", start_date=start_date, to_numeric=True)["Labor Force Level"].iloc[-1]
    lfpr = get_fred_data("CIVPART", "LFPR", start_date=start_date, to_numeric=True, to_datetime=True).set_index("date")
    current_lfpr = lfpr["LFPR"].iloc[-1]
    current_lfpr_date = lfpr["LFPR"].index[-1].strftime("%B %Y")
    pre_covid_lfpr = lfpr.loc["2020-02-01", "LFPR"]
    lfpr_change = current_lfpr - pre_covid_lfpr
    # outside of the pandemic, when was the last time the LFPR was this low?
    lowest_before_pandemic = lfpr.query("date < '2020-01-01' & LFPR <= @current_lfpr").iloc[-1]
    lowest_before_pandemic_val = lowest_before_pandemic["LFPR"]
    lowest_before_pandemic_val = f"also {lowest_before_pandemic_val}%" if lowest_before_pandemic_val == current_lfpr else lowest_before_pandemic_val
    lowest_before_pandemic_date = lowest_before_pandemic.name.strftime("%B %Y")
    # adjusting for population gains, not totally sure how this works
    pop = get_fred_data("CNP16OV", "Population", start_date=start_date, to_numeric=True, to_datetime=True).set_index('date') #BLS pop, monthly
    precov_pop =  pop.loc["2020-02-01"].values[0]
    adjusted_pop = round(((precov_pop)*(abs(lfpr_change) / 100) / 1_000), 2)
    ## Return
    return {
        "unemployment": unemployment,
        "job_openings": job_openings,
        "real_earnings_biden": real_earnings_biden,
        "real_earn_change": real_earn_change,
        "current_real_earn": current_real_earn,
        "current_lfpr": current_lfpr,
        "current_lfpr_date": current_lfpr_date,
        "lowest_before_pandemic_val": lowest_before_pandemic_val,
        "lowest_before_pandemic_date": lowest_before_pandemic_date,
        "lfpr_change": round(lfpr_change, 1),
        "adjusted_pop": adjusted_pop,
        "labor_level": round(labor_level / 1_000, 1) 
    }

## INTEREST RATES ##
def get_interest_data():
    ## 10 year treasury YIELD
    treasury_10 = get_fred_data("DGS10", "10yr Treasury Yield", to_float=True).dropna() # daily
    treasury_10_now = treasury_10["10yr Treasury Yield"].iloc[-1].round(1)
    treasury_10_biden_start = treasury_10[treasury_10["date"].str[:-3] == "2021-01"]["10yr Treasury Yield"].mean().round(1)
    ## Federal Funds target rate
    fed_target_lower = get_fred_data("DFEDTARL", "Fed Funds Target Lower", to_numeric=True, to_datetime=True)
    fed_target_upper = get_fred_data("DFEDTARU", "Fed Funds Target Upper", to_numeric=True, to_datetime=True)
    fed_target_lower_now = fed_target_lower["Fed Funds Target Lower"].iloc[-1]
    fed_target_upper_now = fed_target_upper["Fed Funds Target Upper"].iloc[-1]
    fed_target_lower_biden_start = fed_target_lower[fed_target_lower["date"] >= "2021-01-20"]["Fed Funds Target Lower"].iloc[0]
    fed_target_upper_biden_start = fed_target_upper[fed_target_upper["date"] >= "2021-01-20"]["Fed Funds Target Upper"].iloc[0]
    ## Return
    return {
        "treasury_10_now": treasury_10_now,
        "treasury_10_biden_start": treasury_10_biden_start,
        "fed_target_lower_now": fed_target_lower_now,
        "fed_target_upper_now": fed_target_upper_now,
        "fed_target_lower_biden_start": fed_target_lower_biden_start,
        "fed_target_upper_biden_start": fed_target_upper_biden_start
    }

## GAS AND OIL ##
def get_gas_oil_data():
    gas = get_fred_data("GASREGW", "gas_price", to_numeric=True).set_index("date")
    gas_trump_average = gas["2017-01-01":"2021-01-20"]["gas_price"].mean().round(2)
    gas_now = gas["gas_price"].iloc[-1].round(2)
    oil = get_fred_data("DCOILWTICO", "oil_price", to_numeric=True).set_index("date")
    oil_trump_average = oil["2017-01-01":"2021-01-20"]["oil_price"].mean()
    oil_now = oil["oil_price"].iloc[-1]
    ## Return
    return {
        "gas_trump_average": gas_trump_average,
        "gas_now": gas_now,
        "oil_trump_average": oil_trump_average,
        "oil_now": oil_now
    }

print("Summary stats helper functions retrieved.")