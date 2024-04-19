
#### GET DEBT ####
import pandas as pd
from datetime import date
import requests
from full_fred.fred import Fred
import streamlit as st

FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
import os
os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")

### SETUP ###
thisyear = date.today().year
today = date.today()
biden_start = date(2021,1,20)
biden_days = (today - biden_start).days
year_ago = date(today.year-1, today.month, today.day).strftime('%Y-%m-%d')

### Treasury API ###
#get debt data
treasury_link = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=10000'
p = requests.get(treasury_link)
data = p.json()
debt_df = pd.DataFrame(data['data'])
debt_df['tot_pub_debt_out_amt'] = debt_df['tot_pub_debt_out_amt'].astype(float)
since_biden = debt_df[debt_df['record_date'] >= '2021-01-20'] #filter to since biden
debt_df.set_index('record_date', inplace=True) #so we can use asof(x) method

### FRED ###
population = fred.get_series_df('POPTOTUSA647NWDB', observation_start=biden_start)
households = fred.get_series_df('TTLHH', observation_start=biden_start)
child_population = 72325602 #from census bureau ACS 2022

### DEBT/POPULATION VALUES ###
# Current
current_debt = debt_df['tot_pub_debt_out_amt'].iloc[-1]
current_debt_rounded = round(current_debt/1e+12, 2)
current_population = int(population['value'].iloc[-1])
current_households = float(households['value'].iloc[-1])*1000
current_child_population = child_population
# Biden Start
biden_start_debt = since_biden['tot_pub_debt_out_amt'].iloc[0]
biden_start_debt_rounded = round(biden_start_debt/1e+12, 2)
# Year Ago
year_ago_index = debt_df.index.asof(year_ago)
debt_year_ago = debt_df.loc[year_ago_index, 'tot_pub_debt_out_amt']

### CALCULATIONS ###
# Americans
debt_per_person = round(current_debt / current_population)
debt_per_household = round(current_debt / current_households)
debt_per_child = round(current_debt / current_child_population)
# Since Biden
biden_debt = current_debt - biden_start_debt
biden_debt_rounded = round(biden_debt/1e+12, 2)
biden_debt_per_person = round(biden_debt / current_population)
biden_debt_per_household = round(biden_debt / current_households)
biden_debt_per_child = round(biden_debt / current_child_population)
# Rate of Change Under Biden
biden_debt_per_day = biden_debt/biden_days
biden_debt_per_day_rounded = round((biden_debt_per_day)/1e+9, 2)
biden_debt_per_hour = round((biden_debt_per_day/1e+6) / 24)
biden_debt_per_min = round(biden_debt_per_day/1e+6/(60*24), 2)
biden_debt_per_sec = round(biden_debt_per_day/(60*60*24))
# Rate of Change Year Ago
debt_increase_from_year_ago = current_debt - debt_year_ago #actual
debt_increase_from_year_ago_rounded = round(debt_increase_from_year_ago/1e+12, 2) #in trillions
debt_year_ago_rounded = round(debt_year_ago/1e+12, 2) #in trillions
last_year_debt_per_day = debt_increase_from_year_ago/365 #actual
last_year_debt_per_day_rounded = round((last_year_debt_per_day)/1e+9, 2) #in billions
last_year_debt_per_hour = round(last_year_debt_per_day/1e+6 / 24) #in millions
last_year_debt_per_min = round(last_year_debt_per_day/1e+6 /(60*24), 2) #in millions
last_year_debt_per_sec = round(last_year_debt_per_day / (60*60*24)) #in millions
