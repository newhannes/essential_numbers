#### DEBT ACCUMULATION RATE SINCE 1994 ####
import pandas as pd
from datetime import date
import requests
import plotly.express as px
import datetime
import streamlit as st
### Treasury API ###

# Get debt data
treasury_link = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=10000'
p = requests.get(treasury_link)
data = p.json()
debt_df = pd.DataFrame(data['data'])

# Clean debt data
debt_df['tot_pub_debt_out_amt'] = debt_df['tot_pub_debt_out_amt'].astype(float)
debt_df = debt_df[['record_date','tot_pub_debt_out_amt']]#.query("record_date > '2020-01-01'") #filter to 2020
debt_df["record_date"] = pd.to_datetime(debt_df["record_date"])
debt_df["date_year_ago"] = debt_df["record_date"] - pd.DateOffset(years=1)

# Get the debt from a year ago (or the closest date to a year ago)
debt_df.set_index("record_date", inplace=True) # Set 'record_date' as the index
debt_df["debt_year_ago"] = debt_df["date_year_ago"].apply(lambda x: debt_df["tot_pub_debt_out_amt"].asof(x)) # Use 'asof' to find the closest date
debt_df.reset_index(inplace=True)

# Calculate Rate of Increase
debt_df["year_increase"] = debt_df["tot_pub_debt_out_amt"] - debt_df["debt_year_ago"]
debt_df['day_increase'] = debt_df['year_increase'] / 365
debt_df['hour_increase'] = debt_df['year_increase'] / 365 / 24
debt_df['minute_increase'] = debt_df['year_increase'] / 365 / 24 / 60
debt_df['second_increase'] = round(debt_df['year_increase'] / 365 / 24 / 60 / 60)

### Plotly ###
fig = px.line(debt_df, x='record_date', y='second_increase')
fig.update_xaxes(title_text='',showgrid=False, tickfont=dict(size=12, family="Montserrat"))
fig.update_yaxes(title_text='<b>Debt Increase per Second</b>', titlefont=dict(family="Montserrat", size=14), tickprefix="$", tickfont=dict(size=12, family="Montserrat"))
fig.update_layout(template='plotly_white', title='<b>Rate of Debt Accumulation Since 1994</b>', titlefont=dict(size=24, family="Montserrat", color="black"), width=800, height=500)
fig.update_traces(line=dict(width=3, color="#004647"), hovertemplate="Date: %{x}<br>Increase per second: %{y}")
