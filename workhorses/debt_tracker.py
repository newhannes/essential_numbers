import streamlit as st
import pandas as pd
from datetime import date
import requests
from full_fred.fred import Fred
#### GET DEBT ####

@st.cache_data
def debt_tracker_main():
    ### SETUP ###
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
    fred = Fred()
    today = date.today()
    biden_start = date(2021,1,20)
    biden_end = date(2024,1,20)
    biden_start_str = '2021-01-20'
    biden_end_str = '2025-01-20'
    biden_days = (biden_end - biden_start).days
    biden_months = biden_days / 30.45 # average month length

    ### Treasury API ###
    # get debt data
    treasury_link = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=10000'
    p = requests.get(treasury_link)
    data = p.json()
    debt_df = pd.DataFrame(data['data'])
    debt_df['tot_pub_debt_out_amt'] = debt_df['tot_pub_debt_out_amt'].astype(float)

    ### FRED ###
    population = fred.get_series_df('POPTOTUSA647NWDB', observation_start=biden_start)
    households = fred.get_series_df('TTLHH', observation_start=biden_start)
    child_population = 72_648_436 #from census bureau ACS 2023 1-yr estimate DP05 Under-18 years 

    ### DEBT/POPULATION VALUES ###
    # Current
    current_debt = debt_df['tot_pub_debt_out_amt'].iloc[-1]
    current_debt_rounded = round(current_debt/1e+12, 2)
    current_population = int(population['value'].iloc[-1])
    current_households = float(households['value'].iloc[-1])*1000
    current_child_population = child_population
    # Biden Start
    biden_start_debt = debt_df.loc[debt_df["record_date"] == biden_start_str, "tot_pub_debt_out_amt"].values[0]
    biden_start_debt_rounded = round(biden_start_debt/1e+12, 2)
    # Biden End
    biden_end_debt = debt_df.loc[debt_df["record_date"] <= biden_end_str, "tot_pub_debt_out_amt"].values[-1] # last value before end date
    biden_end_debt_rounded = round(biden_end_debt/1e+12, 2)
    # Year Ago
    debt_df['record_date'] = pd.to_datetime(debt_df['record_date'])
    most_recent_date = debt_df['record_date'].iloc[-1]
    debt_df.set_index('record_date', inplace=True) #so we can use asof(x) method
    year_ago = most_recent_date - pd.DateOffset(years=1)
    year_ago_index = debt_df.index.asof(year_ago)
    debt_year_ago = debt_df.loc[year_ago_index, 'tot_pub_debt_out_amt']

    ### CALCULATIONS ###
    # Americans
    debt_per_person = round(current_debt / current_population)
    debt_per_household = round(current_debt / current_households)
    debt_per_child = round(current_debt / current_child_population)
    # Since Biden
    biden_debt = biden_end_debt - biden_start_debt
    biden_debt_rounded = round(biden_debt/1e+12, 2)
    biden_debt_per_person = round(biden_debt / current_population)
    biden_debt_per_household = round(biden_debt / current_households)
    biden_debt_per_child = round(biden_debt / current_child_population)
    # Rate of Change Under Biden
    biden_debt_per_month = round(biden_debt/1e9 / biden_months)
    biden_debt_per_day = biden_debt/biden_days
    biden_debt_per_day_rounded = round(biden_debt_per_day/1e+9, 1)
    biden_debt_per_hour = round(biden_debt_per_day/1e+6 / 24)
    biden_debt_per_min = round(biden_debt_per_day/1e+6/(60*24), 1)
    biden_debt_per_sec = round(biden_debt_per_day/(60*60*24))
    # Rate of Change Year Ago
    debt_increase_from_year_ago = current_debt - debt_year_ago #actual
    debt_increase_from_year_ago_rounded = round(debt_increase_from_year_ago/1e+12, 2) #in trillions
    debt_year_ago_rounded = round(debt_year_ago/1e+12, 2) #in trillions
    last_year_debt_per_month = round(debt_increase_from_year_ago/1e9 / 12) #in billions
    last_year_debt_per_day = debt_increase_from_year_ago/365 #actual
    last_year_debt_per_day_rounded = round((last_year_debt_per_day)/1e+9, 1) #in billions
    last_year_debt_per_hour = round(last_year_debt_per_day/1e+6 / 24) #in millions
    last_year_debt_per_min = round(last_year_debt_per_day/1e+6 /(60*24), 1) #in millions
    last_year_debt_per_sec = round(last_year_debt_per_day / (60*60*24)) #actual

    #Store all variables in a dictionary
    debt_dict = {"today":today,
                'current_debt_rounded':current_debt_rounded,
                'debt_per_person':debt_per_person,
                'debt_per_household':debt_per_household,
                'debt_per_child':debt_per_child,
                'biden_start_debt_rounded':biden_start_debt_rounded,
                'biden_end_debt_rounded':biden_end_debt_rounded,
                'biden_debt_rounded':biden_debt_rounded,
                'biden_debt_per_person':biden_debt_per_person,
                'biden_debt_per_household':biden_debt_per_household,
                'biden_debt_per_child':biden_debt_per_child,
                'biden_debt_per_month':biden_debt_per_month,
                'biden_debt_per_day_rounded':biden_debt_per_day_rounded,
                'biden_debt_per_hour':biden_debt_per_hour,
                'biden_debt_per_min':biden_debt_per_min,
                'biden_debt_per_sec':biden_debt_per_sec,
                'debt_year_ago_rounded':debt_year_ago_rounded,
                'debt_increase_from_year_ago_rounded':debt_increase_from_year_ago_rounded,
                'last_year_debt_per_month':last_year_debt_per_month,
                'last_year_debt_per_day_rounded':last_year_debt_per_day_rounded,
                'last_year_debt_per_hour':last_year_debt_per_hour,
                'last_year_debt_per_min':last_year_debt_per_min,
                'last_year_debt_per_sec':last_year_debt_per_sec}
    return debt_dict