############ ----------- Labor Data ----------- ############
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib.dates as mdates
from datetime import datetime
from functools import reduce
import pyperclip 
import html2text
#FRED
from full_fred.fred import Fred
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()

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

def num_formatter(number, format_dict):
    round, units, percent, currency = format_dict.values()
    if currency:
        number = f"${number:,.{round}}"
    elif percent:
        number = f"{number:.{round}f}%"
    elif units:
        number = f"{number:,.{round}f} {units}"
    else:
        number = f"{number:,.{round}f}"
    return number
    



### --- Jobs Data from FRED --- ###
# Total employment
jobs = get_fred_data("PAYEMS", "Total Employment (nonfarm)", to_numeric=True)
jobs["Jobs Added"] = jobs["Total Employment (nonfarm)"].diff() * 1000
# Unemployment 
unemployment_rate = get_fred_data("UNRATE", "Unemployment", to_numeric=True)
unemployment = get_fred_data("UNEMPLOY", "Total Unemployed", to_numeric=True)
# Labor force participation rate
lfbr = get_fred_data("CIVPART", "Labor Force Participation Rate", to_numeric=True) 
# Job Openings THIS IS JOLTS
job_openings = get_fred_data("JTSJOL", "Job Openings", to_numeric=True)
# Average hourly earnings, private employees (percent change yoy)
avg_hourly_earnings = get_fred_data("CES0500000003", "Average Hourly Earnings Increase From Previous Year", units="pc1", to_float=True, errors="ignore")
### --- Merge Data --- ###
list_of_dfs = [jobs, unemployment_rate, lfbr, unemployment, avg_hourly_earnings, job_openings]

jobs_data = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), list_of_dfs)
jobs_data['date'] = pd.to_datetime(jobs_data['date'])
jobs_data["Average Hourly Earnings Increase From Previous Year"] = jobs_data["Average Hourly Earnings Increase From Previous Year"].replace('.', float('nan')).astype(float)
#jobs_data["Month Year"] = (jobs_data['date'].dt.strftime('%B %Y'))
#jobs_data = jobs_data.drop(columns=['date'])
jobs_data = jobs_data.set_index('date')
jobs_data = jobs_data.loc[jobs_data.index >= "1974-01-01"] # past 50 years

#Prep for display

jobs_data['Total Employment (nonfarm)'] = jobs_data['Total Employment (nonfarm)'] / 1000
jobs_data['Total Unemployed'] = jobs_data['Total Unemployed'] / 1000
jobs_data['Job Openings'] = jobs_data['Job Openings'] / 1000
jobs_data["Average Hourly Earnings Increase From Previous Year"] = round(jobs_data["Average Hourly Earnings Increase From Previous Year"],1) 
formatter_dict = {"Total Employment (nonfarm)": {'round': 1, "units": "million", "percent": False, "currency": False},
                    "Jobs Added": {'round': 0, "units": None, "percent": False, "currency": False},
                    "Unemployment": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Total Unemployed": {'round': 2, "units": "million", "percent": False, "currency": False},
                    "Labor Force Participation Rate": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Job Openings": {'round': 2, "units": "million", "percent": False, "currency": False},
                    "Average Hourly Earnings Increase From Previous Year": {'round': 1, "units": None, "percent": True, "currency": False}}



### --- Streamlit --- ###
st.markdown('<h1 style="text-align: center;">Employment and Wages</h1>', unsafe_allow_html=True)



if st.checkbox("Dynamic Report"):
    for col in jobs_data.columns:
        data = jobs_data[col]
        data = data.dropna()
        month = data.index[-1].strftime("%B")
        current = data.iloc[-1]
        last_month = data.index[-2].strftime("%B")
        previous = data.iloc[-2]
        format = formatter_dict[col]
        st.write(f"## {col}")
        columns = st.columns(3)
        with columns[0]:
            st.metric(label=month, value=num_formatter(current, format), delta=round(current - previous,3))
        with columns[1]:
            st.metric(label=last_month, value=num_formatter(previous, format))
        with columns[2]:
            st.metric(label = f"Average Since {data.index[0].year}", value=num_formatter(data.mean(), format))
        st.write("#### Past Year")
        st.line_chart(data.iloc[-12:])

if st.checkbox("Show Raw Data",):
    st.write(jobs_data)


if st.checkbox("Static Report"):
    final_report = ""
    for col in jobs_data.columns:
        # Get variable data
        data = jobs_data[col]
        data = data.dropna()
        current = data.iloc[-1]
        previous = data.iloc[-2]
        format = formatter_dict[col]
        past_data = data.loc[:data.index[-1]]
        
        # Find the closest past entries that have values higher and lower than the current value
        closest_higher = past_data[past_data > current].last_valid_index()
        closest_lower = past_data[past_data < current].last_valid_index()
        if pd.isna(closest_higher):
            highest = "This is the highest value recorded for this variable."
        else:
            closest_higher_value = data.loc[closest_higher]
            highest = (f"Highest value since {closest_higher.strftime('%B %Y')} which was {num_formatter(closest_higher_value, format)}")
        if pd.isna(closest_lower):
            lowest = "This is the lowest value recorded for this variable."
        else:
            closest_lower_value = data.loc[closest_lower]
            lowest = f"Lowest value since {closest_lower.strftime('%B %Y')} which was {num_formatter(closest_lower_value, format)}"
    # Display
#         st.markdown(f"### {col}")
#         st.markdown(f"""- **{data.index[-1].strftime("%B")}:** {num_formatter(current, format)}
# - **Previous:** {num_formatter(previous, format)}
# - **Context:**
#     - {highest}
#     - {lowest}
#     - Average Since {data.index[0].year}: {num_formatter(data.mean(), format)}""")

    # st.markdown(f"<h3 style='margin-bottom:0px;'>{col}</h3>", unsafe_allow_html=True)
    # st.markdown(f"""<ul style='margin-top:-17px;'>
    # <li><b>{data.index[-1].strftime("%B")}:</b> {num_formatter(current, format)}</li>
    # <li><b>Previous:</b> {num_formatter(previous, format)}</li>
    # <li><b>Context:</b>
    #     <ul>
    #     <li>{highest}</li>
    #     <li>{lowest}</li>
    #     <li>Average since {data.index[0].year}: {num_formatter(data.mean(), format)}</li>
    #     </ul>
    # </li>
    # </ul>""", unsafe_allow_html=True)

    # Generate the report text
        report_text = f"""
        <h3 style='margin-bottom:0px;'>{col}</h3>
        <ul style='margin-top:-17px;'>
            <li><b>{data.index[-1].strftime("%B")}:</b> {num_formatter(current, format)}</li>
            <li><b>Previous:</b> {num_formatter(previous, format)}</li>
            <li><b>Context:</b>
                <ul>
                <li>{highest}</li>
                <li>{lowest}</li>
                <li>Average since {data.index[0].year}: {num_formatter(data.mean(), format)}</li>
                </ul>
            </li>
        </ul>
        """
        final_report += report_text
    if st.button("Copy to clipboard"):
        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        plain_text = text_maker.handle(final_report)
        plain_text = plain_text.replace("**", "").replace("###", "").replace("*", "-")
        pyperclip.copy(plain_text)
        st.success("Report copied to clipboard")
    st.markdown(final_report, unsafe_allow_html=True)