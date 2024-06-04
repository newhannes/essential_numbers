##### ----- Automate the update of stats for JCA ----- #####
import pandas as pd
import os
import shutil
from functools import reduce
import streamlit as st
from workhorses.debt_tracker import debt_tracker_main
#FRED
from full_fred.fred import Fred
from datetime import date
FRED_API_KEY =st.secrets["FRED_API_KEY"]
fred = Fred()
@st.cache_data
def get_fred_data(series_id, nickname, start_date=None, end_date=None, frequency=None, units=None, to_datetime=False, to_numeric=False, to_float=False, errors="raise", yoy=False, mom=False):
    data = fred.get_series_df(series_id, observation_start=start_date, observation_end=end_date, frequency=frequency, units=units)
    data = data.drop(columns=['realtime_start', 'realtime_end']).rename(columns={'value': nickname})
    if to_datetime:
        data["date"] = pd.to_datetime(data['date'])
    if to_numeric:
        data[nickname] = pd.to_numeric(data[nickname], errors=errors)
    if to_float:
        data[nickname] = data[nickname].replace('.', float('nan')).astype(float, errors=errors)
    if yoy:
        data[f"{nickname} YoY"] = round(data[nickname].pct_change(periods=12) * 100, 1)
    if mom:
        data[f"{nickname} MoM"] = round(data[nickname].pct_change() * 100, 1)
    return data

#### ==== INFLATION ==== ####
## Get Fred Data ###
# CPI
cpi = get_fred_data("CPIAUCSL", "CPI", yoy=True, to_numeric=True)
core_cpi = get_fred_data("CPILFESL", "Core CPI", to_numeric=True, yoy=True)
# Consumer Expenditures
exp_fam_four = get_fred_data("CXUTOTALEXPLB0506M", "Avg CE HH4", to_numeric=True, to_datetime=True)
exp_fam_four["year"] = exp_fam_four["date"].dt.year
exp_fam_four.set_index("year", inplace=True)
# Merge
list_of_dfs = [cpi, core_cpi]
combined = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), list_of_dfs)
combined["date"] = pd.to_datetime(combined["date"])
combined = combined.set_index("date")
# Past 50yrs Only
combined = combined.loc["1974-01-01":]
## YoY
topline = combined["CPI YoY"].iloc[-1]
## Core inflation
core = combined["Core CPI YoY"].iloc[-1]
## Cumulative under Biden
biden_inflation = round((combined.iloc[-1]["CPI"] - combined.loc["January 2021", "CPI"])/ combined.loc["January 2021", "CPI"] * 100,1).values[0]
## Peak pandemic inflation
peak_pandemic = combined.loc["June 2022", "CPI YoY"].values[0]
### Cost per month
kole_ce = exp_fam_four.loc[2020:2021]["Avg CE HH4"].mean() #this is the average of CE for 2020 and 2021. Idk why its done this way. 
kole_inc = kole_ce * (biden_inflation / 100 + 1) - kole_ce #take kole_ce and multiply by bidenflation. then subtract kole_ce to get the increase.
mon_kole_inc = kole_inc / 12
    ####more than how many car payments
    ####more than what mortgage
    ####more than how many student loan payments
inflation_html = f"""
<ul>
    <li>Topline Inflation: <strong>{topline}%</strong></li>
    <li>Core Inflation: <strong>{core}%</strong></li>
    <li>Peak Pandemic Inflation (June-2022): <strong>{peak_pandemic}%</strong></li>
    <li>Cumulative Inflation under Biden: <strong>{biden_inflation}%</strong></li>
    <li>Inflation costs per month (family of four): <strong>${mon_kole_inc:,.0f}</strong></li>
</ul>
"""

#### ===== INTEREST RATES ===== ####
## 30 year fixed MORTGAGE
mortgage_rate = get_fred_data("MORTGAGE30US", "30yr Mortgage Rate", to_numeric=True)
mortgage_rate = mortgage_rate["30yr Mortgage Rate"].iloc[-1]
## 10 year treasury YIELD
treasury_10 = get_fred_data("DGS10", "10yr Treasury Yield", to_float=True)
treasury_10 = treasury_10["10yr Treasury Yield"].iloc[-1]
## EFFECTIVE FEDERAL FUNDS RATE 
fed_fun = get_fred_data("FEDFUNDS", "Fed Funds Rate", to_numeric=True)
fed_fun = fed_fun["Fed Funds Rate"].iloc[-1]
# Interest Projections on the debt
## Now
interest_now = 870
## 10 years
interest_10 = 1.6
## 30 years 
interest_30 = 5.4

interest_html = f"""
<ul>
    <li>30-year Fixed Rate Mortgage: <strong>{mortgage_rate}%</strong></li>
    <li>10-year Treasury Yield: <strong>{treasury_10}%</strong></li>
    <li>Federal Funds Rate: <strong>{fed_fun}%</strong></li>
    <li>Interest projections on debt now (2024): <strong>${interest_now} billion</strong></li>
    <li>Interest projections on the debt in 10 years: <strong>${interest_10} trillion</strong></li>
    <li>Interest projections on the debt in 30 years: <strong>${interest_30} trillion</strong></li>
</ul>
"""

#### ==== LABOR MARKET ==== ####
## Unemployment
unemployment = get_fred_data("UNRATE", "Unemployment Rate", to_numeric=True)
unemployment = unemployment["Unemployment Rate"].iloc[-1]
## Job Openings
job_openings = get_fred_data("JTSJOL", "Job Openings", to_numeric=True)
job_openings = job_openings["Job Openings"].iloc[-1]
# - Real Earnings (take 2) - #
# Get and Clean Data
earnings = get_fred_data("CES0500000011", "Earnings", to_numeric=True, yoy=False)
earnings = earnings.merge(cpi, on="date", how="left")
earnings["date"] = pd.to_datetime(earnings["date"], format="%Y-%m-%d")
earnings["YoY Increase"] = earnings["Earnings"].diff(periods=12)
# Calculations
earnings["CPI Multiplier"] = earnings["CPI"].iloc[-1] / earnings["CPI"]
earnings["Real Earnings, Today's Dollars"] = round(earnings["Earnings"] * earnings["CPI Multiplier"], 2) #take the real earnings and multiply by the CPI ratio to get the real earnings in today's dollars
# Stats
biden_real_earn = earnings.loc[earnings["date"] == "2021-01-01", "Real Earnings, Today's Dollars"].values[0]
current_real_earn = earnings["Earnings"].iloc[-1]
real_earn_change = round(((biden_real_earn/current_real_earn)-1)*100,2)
real_earnings_biden = round(100 - ((current_real_earn / biden_real_earn) * 100), 1)
##Relative to when President Biden took office in January 2021, real earnings are down {real_earnings_biden}%.
# Labor markert
start_date = "1974-01-01"
labor_level = get_fred_data("CLF16OV", "Labor Force Level", start_date=start_date, to_numeric=True)
lfpr = get_fred_data("CIVPART", "LFPR", start_date=start_date, to_numeric=True, to_datetime=True).set_index("date")
current_lfpr = lfpr["LFPR"].iloc[-1]
current_lfpr_date = lfpr["LFPR"].index[-1].strftime("%B %Y")
pre_covid_lfpr = lfpr.loc["2020-02-01", "LFPR"]
lbfr_change = current_lfpr - pre_covid_lfpr
#outside of the pandemic, when was the last time the LFPR was this low?
lowest_before_pandemic = lfpr.query("date < '2020-01-01' & LFPR < @current_lfpr").iloc[-1]
lowest_before_pandemic_date = lowest_before_pandemic.name.strftime("%B %Y")
#adjusting for population gains, not totally sure how this works
pop = get_fred_data("CNP16OV", "Population", start_date=start_date, to_numeric=True, to_datetime=True).set_index('date') #BLS pop, monthly
precov_pop =  pop.loc["2020-02-01"].values[0]
adjusted_pop = round(((precov_pop)*(abs(lbfr_change) /100) /1000), 2)
# HTML
labor_html = f"""
<ul>
    <li>Unemployment Rate: <strong>{unemployment}%</strong></li>
    <li>Job Openings: <strong>{job_openings/1000:,.1f} million</strong></li>
    <li>Relative to when President Biden took office in January 2021, real earnings are down <strong>{real_earnings_biden}%</strong>.</li>
    <li>Labor Force Participation Rate {current_lfpr_date}: <strong>{current_lfpr}%</strong></li>
    <li>This is <strong>{abs(lbfr_change):.2f} percentage points</strong> lower than the pre-pandemic rate of {pre_covid_lfpr}% in {lowest_before_pandemic_date}.</li>
    <li>This equates to approximately <strong>{adjusted_pop} million</strong> fewer Americans in the labor force when adjusting for population gains.</li>
</ul>
"""

#### ===== DEBT ===== ####
dt = debt_tracker_main()
basic_debt_html = f"""
<div class = "header">
<h1 style='text-align: center;'>Debt Tracker</h1>
<h3 style='text-align: center;'> As of {dt['today']}</h3>
</div>
        <h2>Current Debt</h2>
        <p>The gross national debt is currently <strong>${dt['current_debt_rounded']:,} trillion</strong>. This equates to:</p>
        <ul>
            <li><strong>${dt['debt_per_person']:,}</strong> per person</li>
            <li><strong>${dt['debt_per_household']:,}</strong> per household</li>
            <li><strong>${dt['debt_per_child']:,}</strong> per child</li>
        </ul>
        <h2>Debt Accumulation under President Biden</h2>
        <p>When President Biden took office total gross debt was <strong>${dt['biden_start_debt_rounded']:,} trillion</strong>, meaning he has increased the national debt by <strong>${dt['biden_debt_rounded']:,} trillion</strong>. This equates to:</p>
        <ul>
            <li><strong>${dt['biden_debt_per_person']:,}</strong> more debt per person</li>
            <li><strong>${dt['biden_debt_per_household']:,}</strong> more debt per household</li>
            <li><strong>${dt['biden_debt_per_child']:,}</strong> more debt per child</li>
        </ul>
        <p>The rate of debt accumulation during the Biden Administration has equaled:</p>
        <ul>
            <li><strong>${dt['biden_debt_per_month']:,} billion</strong> in new debt per month</li>
            <li><strong>${dt['biden_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['biden_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['biden_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['biden_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
        <h2>Debt Accumulation in Past Year</h2>
        <p>The debt one year ago was <strong>${dt['debt_year_ago_rounded']:,} trillion</strong>, meaning that the debt has increased by <strong>${dt['debt_increase_from_year_ago_rounded']:,} trillion</strong> over the past 12 months. This rate of increase equates to:</p>
        <ul>
            <li><strong>${dt['last_year_debt_per_month']:,} billion</strong> in new debt per month</li>
            <li><strong>${dt['last_year_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['last_year_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['last_year_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['last_year_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
"""


#### ==== FINAL HTML ==== ####
# Image path
# st.write(os.getcwd())
# st.write(os.listdir())
# os.chdir("inputs")
# st.write(os.getcwd())
# st.write(os.listdir())
image_path = "/mount/src/essential_numbers/inputs/HBR_Logo_Primary.png"
st.image(image_path)
style = f"""
<!DOCTYPE html>
    <html>
    <head>
        <center>
            <img src={image_path} width = "70%" align = "middle">
        </center> 
        <title>JCA Quick Stats</title>
        <style>
            body {{
                font-family: 'Montserrat', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f7f7f7;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #004647;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                margin-top: 20px;
            }}
            .content h2 {{
                color: #004647;
            }}
            .content p {{
                color: #333;
            }}
            .content img {{
                width: 90%;
                margin-top: 20px;
            }}
        </style>
""" 
final_html = f"""
{style}
<div class="header">
    <h1 style='text-align: center;'>JCA Quick Stats</h1>
    <h2 style='text-align: center;'>{date.today().strftime("%B %d, %Y")}</h2>
</div>
<div class="container">
    <div class="content">
        <h2>Inflation</h2>
        {inflation_html}
        <h2>Interest Rates</h2>
        {interest_html}
        <h2>Labor Market</h2>
        {labor_html}
        {basic_debt_html}
    </div>
</div>
"""

st.markdown(final_html.replace(style,""), unsafe_allow_html=True)

import pdfkit
pdf = pdfkit.from_string(final_html, False, options={"enable-local-file-access": ""})
# Add a button to download the PDF
st.download_button(
    "⬇️ Download PDF",
    data=pdf,
    file_name=f"JCA Quick Stats {dt['today']}.pdf",
    mime="application/octet-stream"
)