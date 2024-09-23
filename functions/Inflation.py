######## ----------- Inflation Page -------------- ########
import streamlit as st
import pandas as pd
from functools import reduce
import pyperclip
import html2text
#FRED
from full_fred.fred import Fred
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()

def get_fred_data(series_id, nickname, start_date=None, end_date=None, frequency=None, units=None, to_datetime=False, to_numeric=False, to_float=False, errors="raise", yoy=False, mom=False):
    data = fred.get_series_df(series_id, observation_start=start_date, observation_end=end_date, frequency=frequency, units=units)
    data = data.drop(columns=['realtime_start', 'realtime_end']).rename(columns={'value': nickname})
    if to_datetime:
        data["date"] = pd.to_datetime(data['date'])
    if to_numeric:
        data[nickname] = pd.to_numeric(data[nickname], errors=errors)
    if to_float:
        data[nickname] = data[nickname].astype(float, errors=errors)
    if yoy:
        data[f"{nickname} YoY"] = round(data[nickname].pct_change(periods=12) * 100, 1)
    if mom:
        data[f"{nickname} MoM"] = round(data[nickname].pct_change() * 100, 1)
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


##### ------ Get Fred Data ------ #####
# CPI
cpi = get_fred_data("CPIAUCSL", "CPI", yoy=True, mom=True, to_numeric=True)
core_cpi = get_fred_data("CPILFESL", "Core CPI", to_numeric=True, yoy=True, mom=True)
housing = get_fred_data("CPIHOSNS", "Housing CPI", to_numeric=True, yoy=True, mom=True)
food = get_fred_data("CPIUFDNS", "Food CPI", to_numeric=True, yoy=True, mom=True)
energy = get_fred_data("CPIENGSL", "Energy CPI", to_numeric=True, yoy=True, mom=True)
# Consumer Expenditures
exp_fam_four = get_fred_data("CXUTOTALEXPLB0506M", "Avg CE HH4", to_numeric=True)
exp_fam_four["date"] = pd.to_datetime(exp_fam_four["date"])
exp_fam_four["year"] = exp_fam_four["date"].dt.year
exp_fam_four.set_index("year", inplace=True)
# Merge
list_of_dfs = [cpi, core_cpi, housing, food, energy]
combined = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), list_of_dfs)
combined["date"] = pd.to_datetime(combined["date"])
combined = combined.set_index("date")
# Past 50yrs Only
combined = combined.loc["1974-01-01":]
###### ------- Calculations and Currents ------- ######
kole_ce = exp_fam_four.loc[2020:2021]["Avg CE HH4"].mean() #this is the average of CE for 2020 and 2021. Idk why its done this way. 
biden_inflation = round((combined.iloc[-1]["CPI"] - combined.loc["January 2021", "CPI"])/ combined.loc["January 2021", "CPI"] * 100,1).values[0]
kole_inc = kole_ce * (biden_inflation / 100 + 1) - kole_ce #take kole_ce and multiply by bidenflation. then subtract kole_ce to get the increase.
mon_kole_inc = kole_inc / 12
# Food, energy, housing since Biden
food_biden = round((combined.iloc[-1]["Food CPI"] - combined.loc["January 2021", "Food CPI"])/ combined.loc["January 2021", "Food CPI"] * 100,0).values[0]
energy_biden = round((combined.iloc[-1]["Energy CPI"] - combined.loc["January 2021", "Energy CPI"])/ combined.loc["January 2021", "Energy CPI"] * 100,0).values[0]
housing_biden = round((combined.iloc[-1]["Housing CPI"] - combined.loc["January 2021", "Housing CPI"])/ combined.loc["January 2021", "Housing CPI"] * 100,0).values[0]
# Currents
cpi_current = combined.iloc[-1]["CPI YoY"]
core_cpi_current = combined.iloc[-1]["Core CPI YoY"]

####### ------ Streamlit Display ------ #######
st.markdown("<h1 style='text-align: center;'>Inflation Data</h>", unsafe_allow_html=True)

if st.checkbox("Dynamic Report"):
    base_cols = ["CPI YoY", "Core CPI YoY", "Housing CPI YoY", "Food CPI YoY", "Energy CPI YoY"]
    for col in base_cols:
        data = combined[col]
        data = data.dropna()
        month = data.index[-1].strftime("%B")
        current = data.iloc[-1]
        last_month = data.index[-2].strftime("%B")
        previous = data.iloc[-2]
        #format = formatter_dict[col]
        st.write(f"## {col}")
        columns = st.columns(3)
        with columns[0]:
            st.metric(label=month, value=f"{current}%", delta=round(current - previous,3))
        with columns[1]:
            st.metric(label=last_month, value=f"{previous}%")
        with columns[2]:
            st.metric(label = f"Average Since {data.index[0].year}", value=f"{round(data.mean(),1)}%")
        st.write("#### Past Year")
        st.line_chart(data.iloc[-12:])

if st.checkbox("Static Report"):
    
    # Prep for more detailed analysis
    final_report = ""
    formatter_dict = {"CPI YoY": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Core CPI YoY": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Housing CPI YoY": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Food CPI YoY": {'round': 1, "units": None, "percent": True, "currency": False},
                    "Energy CPI YoY": {'round': 1, "units": None, "percent": True, "currency": False}}
    base_cols = ["CPI YoY", "Core CPI YoY", "Housing CPI YoY", "Food CPI YoY", "Energy CPI YoY"]
    # More detailed analysis
    for col in base_cols:
        # Get variable data
        data = combined[col]
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
    # Summary analysis
    st.write("### Summary and Biden")
    current_month = combined.index[-1].strftime("%B %Y")
    st.write(f"Year-over-year CPI inflation as of {current_month} is **{cpi_current}%**")
    st.write(f"Since President Biden took office, prices have increased by **{biden_inflation}%**.")
    st.write(f"- This means that the average family of four is paying an additional **\${kole_inc:,.0f}** per year or **${mon_kole_inc:,.0f}** per month to purchase the same goods and services as in January 2021.")
    st.write(f"- Food prices have increased by **{food_biden:.0f}%**, energy prices have increased by **{energy_biden:.0f}%**, and housing prices have increased by **{housing_biden:.0f}%** since January 2021.")
    st.markdown(final_report, unsafe_allow_html=True)