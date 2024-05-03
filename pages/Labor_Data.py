############ ----------- Labor Data ----------- ############
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib.dates as mdates
from datetime import datetime
from functools import reduce
#FRED
from full_fred.fred import Fred
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
@st.cache_data
def get_fred_data(series_id, nickname, start_date=None, end_date=None, frequency=None, units=None, to_datetime=False, to_numeric=False, to_float=False, errors="raise"):
    data = fred.get_series_df(series_id, observation_start=start_date, observation_end=end_date, frequency=frequency, units=units)
    data = data.drop(columns=['realtime_start', 'realtime_end']).rename(columns={'value': nickname})
    if to_datetime:
        data["date"] = pd.to_datetime(data['date'])
    if to_numeric:
        data[nickname] = pd.to_numeric(data[nickname], errors=errors)
    if to_float:
        data[nickname] = data[nickname].astype(float, errors=errors)
    return data


### --- Jobs Data from FRED --- ###
# Total employment
jobs = get_fred_data("PAYEMS", "Total Employment (nonfarm) (millions)", to_numeric=True)
jobs["Jobs Added (thousands)"] = jobs["Total Employment (nonfarm) (millions)"].diff()
# Unemployment 
unemployment_rate = get_fred_data("UNRATE", "Unemployment", to_numeric=True)
unemployment = get_fred_data("UNEMPLOY", "Total Unemployed (thousands)", to_numeric=True)
# Labor force participation rate
lfbr = get_fred_data("CIVPART", "LFPR", to_numeric=True) 
# Job Openings THIS IS JOLTS
job_openings = get_fred_data("JTSJOL", "Job Openings (millions)", to_numeric=True)
# Average hourly earnings, private employees (percent change yoy)
avg_hourly_earnings = get_fred_data("CES0500000003", "Avg Hourly Earnings Growth YoY", units="pc1", to_float=True, errors="ignore")
### --- Merge Data --- ###
list_of_dfs = [jobs, unemployment_rate, lfbr, unemployment, avg_hourly_earnings, job_openings]

jobs_data = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), list_of_dfs)
jobs_data['date'] = pd.to_datetime(jobs_data['date'])
jobs_data["Avg Hourly Earnings Growth YoY"] = jobs_data["Avg Hourly Earnings Growth YoY"].replace('.', float('nan')).astype(float)
jobs_data = jobs_data.set_index('date')

### --- Streamlit --- ###
st.title("Employment and Wages")
for i in jobs_data.columns:


        data = jobs_data[i]
        data = data.dropna()
        month = data.index[-1].strftime("%B")
        st.write(f"### {i}")
        st.metric(label=month, value=data.iloc[-1], delta=(data.iloc[-1] - data.iloc[-2]).astype(float))
        st.line_chart(data)
