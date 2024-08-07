####### ========== Create Automated Report for GDP release ========== #######
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import beaapi
import datetime
import requests
from bs4 import BeautifulSoup
from full_fred.fred import Fred
import streamlit as st
import os
os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")
# beaky = st.secrets["BEA_API_KEY"]
# FRED_API_KEY = st.secrets["FRED_API_KEY"]
beaky = "6755F5CF-C995-499D-8687-210BBFFEAC16"
FRED_API_KEY = "d54f6f80ebf26f05dafe603646f2f58f"
fred = Fred()
dark_grey = '#3E3E3E'
light_grey = '#D3D3D3'
slightly_dark_grey = '#4F4F4F'
emerald = "#004647"
jade = "#84AE95"
hunter = "#002829"
today = datetime.datetime.today()
fifty_years_ago = str(today.year - 50) + "-01-01"
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

print("Beginning GDP report script...")


##### ===== Helper Functions ===== #####
def get_or_initialize(var_name, init_func):
    if var_name not in globals():
        print("Initializing", var_name)
        globals()[var_name] = init_func()
    elif not isinstance(globals()[var_name], pd.DataFrame):
        print("Re-initializing", var_name)
        globals()[var_name] = init_func()
    else:
        print("Using existing", var_name)
    return globals()[var_name]
##### ===== DATA ===== #####
## Params
year = 1974
pct_change = get_or_initialize("pct_change", lambda: beaapi.get_data(beaky, datasetname="NIPA", TableName="T10101", Frequency="Q", Year="X"))
gdp = get_or_initialize("gdp", lambda: beaapi.get_data(beaky, datasetname="NIPA", TableName="T10105", Frequency="Q", Year="X"))
contributors_raw = get_or_initialize("contributors_raw", lambda: beaapi.get_data(beaky, datasetname="NIPA", TableName="T10102", Frequency="Q", Year="X"))

##### ===== SECTION 1: OVERVIEW ===== #####
## Real gdp growth, comparison to 50 year average, growth last quarter, GDP in current dollars
current_q = pct_change.TimePeriod.max()
prior_q = pct_change.TimePeriod.max()[:-1] + str(int(pct_change.TimePeriod.max()[-1]) - 1)
real_gdp = pct_change.query('LineDescription == "Gross domestic product" and TimePeriod == @current_q')["DataValue"].values[0]
real_gdp_last = pct_change.query('LineDescription == "Gross domestic product" and TimePeriod == @prior_q')["DataValue"].values[0] # type: ignore
gdp_nominal = gdp.query('LineDescription == "Gross domestic product" and TimePeriod == @current_q')["DataValue"].values[0] 
fifty_yr_avg = pct_change.loc[(pct_change.LineDescription == "Gross domestic product") & (pct_change.TimePeriod >= "1974Q1"), "DataValue"].mean().round(1)
## Scrape the current GDP release title/type from website
url = "https://www.bea.gov/data/gdp/gross-domestic-product"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
release_title = soup.find(class_="field field--name-field-subtitle field--type-string field--label-hidden field--item").text
release_stage = release_title[release_title.find("(")+1:release_title.find(")")]
current_q_text = release_title[release_title.find(",")+2:release_title.find("2")-1]
## Sentence 
overview_str = f"""
Real GDP grew at an annual rate of {real_gdp} percent in the {current_q_text.lower()} of {current_q[:4]}, according to the Bureau of Economic Analysis's {release_stage.lower()}.  
This is {real_gdp - fifty_yr_avg:.1} percentage points above the 50 year average.
Growth last quarter was {real_gdp_last} percent. GDP now amounts to ${gdp_nominal/1e6:.1f} trillion in current dollars."""

##### ===== SECTION 2: COMPOSITION OF GDP ===== #####
### === Topline contributors to GDP === ###
## Data prep ##
main_contributors = ["Personal consumption expenditures", "Gross private domestic investment", "Net exports of goods and services", "Exports", "Imports", "Government consumption expenditures and gross investment"]
contributors = contributors_raw[contributors_raw["LineDescription"].isin(main_contributors)][["LineDescription", "TimePeriod", "CL_UNIT", "DataValue"]]
rename = ["Consumer spending", "Private investment", "Net exports", "Exports", "Imports", "Government spending and investment"]
rename_dict = dict(zip(main_contributors, rename))
contributors["LineDescription"] = contributors["LineDescription"].map(rename_dict)
contributors = contributors.loc[contributors["TimePeriod"]==contributors["TimePeriod"].max()]
contributors["sign"] = np.where(contributors["DataValue"] > 0, "positive", "negative")
contributors_netexports = contributors.query('LineDescription != "Exports" and LineDescription != "Imports"')
contributors = contributors.query('LineDescription != "Net exports"')
contributors["share of growth"] = (contributors["DataValue"] / contributors["DataValue"].sum() * 100).round(0) #.loc[contributors.sign == "positive", 
## Variables ##
spending = contributors.query('LineDescription == "Consumer spending"')
investment = contributors.query('LineDescription == "Private investment"')
gov = contributors.query('LineDescription == "Government spending and investment"')
exports = contributors.query('LineDescription == "Exports"')
imports = contributors.query('LineDescription == "Imports"')
## Sentence ##
contributors_str = f"""Of the {real_gdp} percent annual growth, consumer spending contributed {spending['DataValue'].values[0]} percentage points, accounting for {spending['share of growth'].values[0]:.0f} percent of total growth.
Private investment contributed {investment['DataValue'].values[0]} percentage points, accounting for {investment['share of growth'].values[0]:.0f} percent of total growth.
Government spending and investment contributed {gov['DataValue'].values[0]} percentage points, accounting for {gov['share of growth'].values[0]:.0f} percent of total growth.
Exports contributed {exports['DataValue'].values[0]} percentage points, accounting for {exports['share of growth'].values[0]:.0f} percent of total growth.
Imports, which are counted against GDP, contributed {imports['DataValue'].values[0]} percentage points from growth, accounting for {imports["share of growth"].values[0]:.0f} percent of total growth."""
### === Chart === ###
### === Plot data === ###
## Prep data
plot1_data = contributors_netexports.pivot(columns="LineDescription", values="DataValue", index="sign")
column_order = plot1_data.sum().sort_values(ascending=False).index
plot1_data = plot1_data[column_order]
total_positive = plot1_data.loc["positive"].sum()
## Setup
fig, ax = plt.subplots(figsize=(9,4))
plt.style.use("housebudget-garet")
plt.rcParams['font.family'] = 'EB Garamond'
start_color = 200
end_color = 10
custom_pal = sns.diverging_palette(start_color, end_color)
sns.set_palette(custom_pal)
## Plot
plot1_data.plot(kind="barh", stacked=True, ax=ax, position=-1, width=0.8)
## Labels
title = f"Percentage point contributions to GDP growth in {contributors_netexports['TimePeriod'].max()}"
ax.set_title(title, fontsize=18, pad=25, x=-0.065, ha='left')
ax.set_ylabel("")
## Format
sns.despine(left=True, bottom=True)
for container in ax.containers:
    labels = [f'{v.get_width():.1f}' if v.get_width() != 0 else '' for v in container]
    ax.bar_label(container, labels=labels, label_type='center', fontweight='bold', fontsize=13)
ax.set_yticks([])
ax.set_xticks([])
ax.legend(loc='center', bbox_to_anchor=(0.5, 1), frameon=False, ncols=4, columnspacing=0.7) # move legend to the top
## Annotations
total_sum = plot1_data.sum().sum() # Calculate the sum of the two bars
bracket_x = plot1_data.sum(axis=1).max()  # Add a bracket
bracket_y = [1.15, 2.25]  
ax.plot([bracket_x+0.3, bracket_x+0.3], bracket_y, color="grey", lw=2)
ax.plot([bracket_x+0.3, bracket_x+0.2], [bracket_y[0], bracket_y[0]], color="grey", lw=2) # add two lines at the end of the bracket
ax.plot([bracket_x+0.3, bracket_x+0.2], [bracket_y[1], bracket_y[1]], color="grey", lw=2)
ax.text(bracket_x+0.4, sum(bracket_y)/2, f'{total_sum:.1f}% growth', fontsize=14, ha='left', va='center', fontweight="bold", color=dark_grey) # Annotate the bracket with the sum
## Fig 
fig_contributors = plt.gcf()
fig.savefig("output/contributors.svg", bbox_inches='tight', dpi=900)

###### ===== SECTION 3: CHANGES THIS QUARTER ===== #####
## Data prep
current_pct_change = pct_change.query('TimePeriod == @current_q')
prior_pct_change = pct_change.query('TimePeriod == @prior_q')
series_codes = ["DPCERL", "DGDSRL", "DSERRL", "A006RL", "A020RL", "A021RL", "A822RL"]
investment_subcats_linenums = [i for i in range(7,14)]
max_investment_subcat = current_pct_change.loc[current_pct_change["LineNumber"].isin(investment_subcats_linenums), "DataValue"].idxmax()
max_investment_subcat = current_pct_change.loc[max_investment_subcat]
## Variables
changes_select = current_pct_change.loc[current_pct_change["SeriesCode"].isin(series_codes)]
consumer_spending = changes_select.loc[changes_select.LineDescription == "Personal consumption expenditures"]
consumer_spending_goods = changes_select.loc[changes_select.LineDescription == "Goods"]
consumer_spending_services = changes_select.loc[changes_select.LineDescription == "Services"]
investment = changes_select.loc[changes_select.LineDescription == "Gross private domestic investment"]
exports = changes_select.loc[changes_select.LineDescription == "Exports"]
imports = changes_select.loc[changes_select.LineDescription == "Imports"]
gov = changes_select.loc[changes_select.LineDescription == "Government consumption expenditures and gross investment"]
## Sentence
changes_str = f"""Consumer spending grew by {consumer_spending.DataValue.values[0]} percent in the {current_q_text.lower()}, with spending on goods increasing by {consumer_spending_goods.DataValue.values[0]} percent and services by {consumer_spending_services.DataValue.values[0]} percent.
Private investment grew by {investment.DataValue.values[0]} percent, with the largest growth in {max_investment_subcat.LineDescription.lower()} investment, which increased by {max_investment_subcat.DataValue} percent.
Exports grew by {exports.DataValue.values[0]} percent, while imports grew by {imports.DataValue.values[0]} percent.
Government spending and investment grew by {gov.DataValue.values[0]} percent."""
### === Chart === ###
## Data prep ##
current_prior = pct_change.query("TimePeriod == @current_q | TimePeriod == @prior_q")[["LineNumber", "SeriesCode", "LineDescription", "TimePeriod", "DataValue"]]
no_consumer_spending = [code for code in series_codes if code != "DPCERL"] # Drop overall consumer spending
current_prior = current_prior.loc[current_prior["SeriesCode"].isin(no_consumer_spending)]
current_prior = current_prior.pivot(index=["SeriesCode", "LineDescription", "LineNumber"], columns="TimePeriod", values="DataValue")
current_prior = current_prior.sort_values("LineNumber")
line_description_replace = {"Services": "Consumer spending, services", "Goods": "Consumer spending, goods", "Gross private domestic investment": "Private investment", "Government consumption expenditures and gross investment": "Government spending and investment"}
plot2_data = current_prior.reset_index().replace({"LineDescription": line_description_replace}).drop(columns="LineNumber").set_index("LineDescription").sort_values(by=current_q, ascending=True)
pal = sns.light_palette(emerald)
## Setup
fig, ax = plt.subplots(figsize=(8,6))
plt.style.use("housebudget-garet")
plt.rcParams['font.family'] = 'EB Garamond'
## Plot
plot2_data.plot(kind="barh", ax=ax, width=0.5, color=[light_grey, pal[-2]])
## Labels
title = f"Growth in key components of GDP in {current_q}"
ax.set_title(title, fontsize=19, pad=25, x=-0.34)
ax.set_ylabel("")
## Format
sns.despine(left=True, bottom=True)
ax.set_xticks([])
ax.yaxis.set_tick_params(width=0)
ax.legend(loc='center', bbox_to_anchor=(-0.145, 1.01), frameon=False, ncol=2)
for ytick in ax.get_yticklabels():
    ytick.set_horizontalalignment('left')
    ytick.set_x(-0.32)
## Label the bars
for i in ax.patches:
    # get_width pulls left or right; get_y pushes up or down
    color = i.get_facecolor() if i.get_facecolor() == (0.1828294484126073, 0.4098312873493175, 0.41315284279564213, 1.0) else slightly_dark_grey
    fontweight = "normal" if color == slightly_dark_grey else "bold"
    ax.text(i.get_width(), i.get_y() + 0.05, f'{i.get_width():.1f}%', fontsize=12, color=color, fontweight=fontweight)
fig_growth_comparison = ax.get_figure()
## Save
fig.savefig("output/growth_comparison.svg", bbox_inches='tight', dpi=900)

##### ===== SECTION 4: PAST TWO YEARS ===== #####
quarter_dict = {'-01-01': 'Q1', '-04-01': 'Q2', '-07-01': 'Q3', '-10-01': 'Q4'}
gdp_growth_rate = get_fred_data("A191RL1Q225SBEA", "gdp_growth_rate", start_date=fifty_years_ago, to_numeric=True)
gdp_growth_rate["quarter-year"] = gdp_growth_rate["date"].str[4:].map(quarter_dict) + " " + gdp_growth_rate["date"].str[:4]
# add a column that records whether the value is bellow or above the historical average
gdp_growth_rate["context"] = gdp_growth_rate["gdp_growth_rate"].apply(lambda x: "above/equal" if x >= round(gdp_growth_rate["gdp_growth_rate"].mean(), 1) else "below")
gdp_since22 = gdp_growth_rate[gdp_growth_rate["date"] >= "2022-01-01"]
gdp_since22 = gdp_since22[['quarter-year', 'gdp_growth_rate', 'context']]
historic_average = gdp_growth_rate['gdp_growth_rate'].mean()
#### -------- Chart Time -------- ####
plt.rcParams['font.family'] = "EB Garamond"
plt.figure(figsize=(12,6))
ax = sns.barplot(data=gdp_since22, x="quarter-year", y="gdp_growth_rate", hue="context", palette=[jade, emerald])
plt.title("Quarterly annualized real GDP growth since Q1 2022", fontsize=19, pad=15)
plt.xlabel("")
plt.xticks(fontsize=13)
plt.ylabel("")
plt.yticks([])
plt.gca().xaxis.set_tick_params(width=0)
for i in ax.containers:
        ax.bar_label(i, labels = [f"{x}%" for x in i.datavalues], weight="bold", fontsize = 13, label_type="edge", padding=1) #add labels to bars
plt.legend(title="Comparison to 50-year average", title_fontsize="12", fontsize="11", loc="upper left", frameon=False)
sns.despine(bottom=True, left=True)
## Store fig as object
fig_past_two_years = plt.gcf()
## Save
fig_past_two_years.savefig("output/gdp_growth_since22.svg", bbox_inches='tight', dpi=900)

##### ====== HTML REPORT ===== #####
html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'EB Garamond', serif;
            color: #3E3E3E;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #004647;
            font-size: 28px;
            margin-top: 20px;
        }}
        h2 {{
            color: #004647;
            font-size: 24px;
            margin-top: 20px;
        }}
        p {{
            font-size: 16px;
            margin-top: 10px;
        }}
        .chart {{
            margin-top: 10px;
        }}
        .source {{
            font-size: 12px;
            color: grey;
            margin-top: 10px;
        }}
        .centered-image {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-top: 20px;
            width: 80%; /* Adjust the width as needed */
        }}
    </style>
</head>

<body>
    <img src="../input/HBR_Logo_Primary.png" class="centered-image" />
    <h1>GDP Report: {current_q_text} {release_stage}</h1>
    <p>{overview_str}</p>
    <h2>Composition of GDP</h2>
    <p>{contributors_str}</p>
    <div class="chart">
        <img src="contributors.svg" />
    </div>
    <h2>Changes this Quarter</h2>
    <p>{changes_str}</p>
    <div class="chart">
        <img src="growth_comparison.svg" />
    </div>
    <h2>GDP Growth Since 2022</h2>
    <div class="chart">
        <img src="gdp_growth_since22.svg" />
    </div>
    <p class="source">Source: Bureau of Economic Analysis</p>
</body>

</html>
"""

with open(f"output/gdp_report_{today.strftime("%d-%m-%y")}.html", "w") as file:
    file.write(html)

print("GDP report script complete!")