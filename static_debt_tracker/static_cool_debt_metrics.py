##### ------------ COOL DEBT METRICS STATIC ------------ #####
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib import ticker
from full_fred.fred import Fred
from datetime import date
import requests 
import json
import tempfile
import streamlit as st
FRED_API_KEY = st.secrets["FRED_API_KEY"]
BLS_API_KEY = st.secrets["BLS_API_KEY"]
fred = Fred()
today = date.today().strftime("%Y-%m-%d")
gold = "#967D4A"
jade = "#84AE95"
emerald = "#004647"
darker_emerald = "#002F2F"

# Create a temporary directory
temp_dir = tempfile.mkdtemp()

#### --------- DEBT TO FEDERAL ASSETS --------- ####
# MARK: DEBT TO ASSETS
## --- Get Data from FRED --- ##
# both are quarterly data 
startdate = "1966-01-01"
financial_assets = fred.get_series_df("FGTFASQ027S", observation_start=startdate, observation_end=today).rename(columns={"value": "Financial Assets"}).drop(columns=["realtime_start", "realtime_end"])
total_debt = fred.get_series_df("GFDEBTN", observation_start=startdate, observation_end=today).rename(columns={"value": "Total Debt"}).drop(columns=["realtime_start", "realtime_end"])
debt_to_assets = total_debt.join(financial_assets, how="inner",  lsuffix='_total_debt', rsuffix='_financial_assets')
debt_to_assets[["Total Debt", "Financial Assets"]] = debt_to_assets[["Total Debt", "Financial Assets"]].apply(pd.to_numeric)
debt_to_assets['debt_to_assets'] = debt_to_assets['Total Debt'] / debt_to_assets['Financial Assets']
debt_to_assets = debt_to_assets[['date_total_debt', "Total Debt", "Financial Assets", "debt_to_assets"]]
debt_to_assets['date_total_debt'] = pd.to_datetime(debt_to_assets['date_total_debt'])

## --- Textual Analysis --- ##
quarter_dict = {1: 'Q1', 2: 'Q1', 3: 'Q1', 4: 'Q2', 5: 'Q2', 6: 'Q2', 7: 'Q3', 8: 'Q3', 9: 'Q3', 10: 'Q4', 11: 'Q4', 12: 'Q4'}
average = round(debt_to_assets['debt_to_assets'].mean(), 1)
most_recent = round(debt_to_assets['debt_to_assets'].iloc[-1],1)
most_recent_date = debt_to_assets['date_total_debt'].iloc[-1]
most_recent_quarter = quarter_dict[int(most_recent_date.month)]
most_recent_year = most_recent_date.year
most_recent_debt = round(debt_to_assets['Total Debt'].iloc[-1] / 1e6, 2)
most_recent_assets = round(debt_to_assets['Financial Assets'].iloc[-1]/1e6, 2)
text_debt_to_assets = f"""
<ul>
    <li>For {most_recent_quarter} {most_recent_year}, the gross federal debt was ${most_recent_debt:,} trillion and the federal asset level was ${most_recent_assets} trillion, a debt to assets ratio of <b>{most_recent}</b>.</li>
    <li>Since 1966, the debt to assets ratio has averaged <b>{average}</b>.</li>
    <li>The current ratio is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period.</li>
</ul>
"""

## DEBT TO ASSETS PLOT ##
## --- Chart Time --- ##
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"

# Create the plot
plt.figure(figsize=(12, 4))
ax = sns.lineplot(x='date_total_debt', y='debt_to_assets', data=debt_to_assets, linewidth=3, color=emerald)
# Set the title and labels
plt.title('Ratio of Gross Debt to Federal Assets Since 1966', fontsize=18, loc="left", fontweight='bold', color="black")
plt.xlabel('')
plt.ylabel("Ratio")
plt.grid(axis="y", alpha=0.3)
sns.despine()
plt.savefig(temp_dir+"/debt_to_assets.png", dpi=600, bbox_inches='tight')


#### -------- RATIO OF DEBT TO TOTAL WAGES -------- ####
# MARK: DEBT TO WAGES
# This is annual data. While BLS has quarterly data, I am having trouble comparing quarterly wages paid to the level of debt in that quarter. 
# I would need to have the debt ADDED in that quarter to compare to the wages PAID in that quarter.
### --- BLS API --- ###
headers = {'Content-type': 'application/json'}
startyear = "2004"
endyear = "2023"

def bls_df(series, startyear, endyear):
    data = json.dumps({"seriesid": series, "startyear": startyear, "endyear": endyear, "catalog": True, "registrationkey": BLS_API_KEY, "annualaverage":True})
    p = requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=data, headers=headers)
    json_data = json.loads(p.text)
    data = {"series_id": [], "year": [], "period": [], "value": [], "footnotes": []}
    for series in json_data['Results']['series']:
        if series['data'] == []:
            print("No data found for series:", series['seriesID'])
        else:
            seriesId = series['seriesID']
            for item in series['data']:
                year = item['year']
                period = item['period']
                value = item['value']
                footnotes = ""
                for footnote in item['footnotes']:
                    if footnote:
                        footnotes = footnotes + footnote['text'] + ','
                data["series_id"].append(seriesId)
                data["year"].append(year)
                data["period"].append(period)
                data["value"].append(value)
                data["footnotes"].append(footnotes[0:-1])
    df = pd.DataFrame(data)
    return df
### --- FRED DEBT per Year --- ###
annual_debt = fred.get_series_df("GFDEBTN", observation_start="2000-01-01", observation_end=today, frequency="a").drop(columns=['realtime_start', 'realtime_end']).rename(columns={"value": "Total Debt"})
annual_debt['Total Debt'] = annual_debt['Total Debt'].astype(float) * 1e6
annual_debt['year'] = annual_debt['date'].str[:4]
### --- Retreieve and Clean BLS Data --- ###
quarterly_wages = bls_df(["ENUUS00030010"], startyear, endyear)
quarterly_wages['value'] = quarterly_wages['value'].astype(float) * 1000
quarterly_wages["quarter-yr"] = quarterly_wages["period"] + "-" + quarterly_wages["year"]
quarterly_wages = quarterly_wages.rename(columns={"value": "Wages"})
annual_wages = quarterly_wages.query("period == 'Q05'")
### --- Merge Data and Calculate Ratio --- ### 
debt_to_wage = annual_debt.merge(annual_wages, on="year", how="inner")
debt_to_wage['debt_to_wages'] = debt_to_wage['Total Debt'] / debt_to_wage['Wages']
debt_to_wage = debt_to_wage[['year', 'Total Debt', 'Wages', 'debt_to_wages']]
### --- Textual Analysis --- ###
average = round(debt_to_wage['debt_to_wages'].mean(), 2)
most_recent = debt_to_wage['debt_to_wages'].iloc[-1]
most_recent_year = debt_to_wage['year'].iloc[-1]
most_recent_wages = debt_to_wage['Wages'].iloc[-1]
most_recent_debt = debt_to_wage['Total Debt'].iloc[-1]
earliest_year = debt_to_wage['year'].iloc[0]
earliest = debt_to_wage['debt_to_wages'].iloc[0]
earliest_debt = debt_to_wage['Total Debt'].iloc[0]
earliest_wages = debt_to_wage['Wages'].iloc[0]
earliest_difference = round((earliest_debt - earliest_wages) / 1e12, 2)
most_recent_difference = round((most_recent_debt - most_recent_wages) / 1e12, 2)
text_debt_to_wages = f"""
<ul>
    <li>In {earliest_year}, the gross debt exceeded total wages paid to U.S. workers by <b>${earliest_difference} trillion </b> and the debt to wage ratio was <b>{round(earliest, 2)}</b>.</li>
    <li>As of {most_recent_year}, the gross debt exceeded total wages by <b>${most_recent_difference} trillion</b> and the debt to wage ratio was <b>{round(most_recent, 2)}</b>, a <b>{round((most_recent - earliest)/earliest *100)}%</b> increase since {earliest_year}.</li>
    <li>Since {earliest_year}, the debt to wage ratio has averaged {average}, the current debt to wage ratio is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period.</li>
    
</ul>
"""
### --- Plot --- ###
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"
plt.figure(figsize=(12, 4))
sns.lineplot(x='year', y='debt_to_wages', data=debt_to_wage, linewidth=3, color=emerald)
plt.title(f'Ratio of Gross Debt to Total Wages Since {earliest_year}', fontsize=18, fontweight='bold', color="black", loc="left")
plt.xlabel('')
plt.xticks(debt_to_wage['year'][::4])
plt.ylabel('Debt to Wages')
sns.despine()
plt.grid(axis='y', alpha=0.3)
plt.savefig(temp_dir+"/debt_to_wages.png", dpi=600, bbox_inches='tight')


#### -------- MORTGAGE RATES/HOUSING PRICES SINCE JAN 2021 -------- ####
# MARK: MORTGAGE
## -- FRED Data -- ##
mortgage_rate = fred.get_series_df("MORTGAGE30US", observation_start="2021-01-20", observation_end=today).drop(columns={'realtime_start', 'realtime_end'}).rename(columns={"value": "Mortgage Rate"})
mortgage_rate['Mortgage Rate'] = mortgage_rate['Mortgage Rate'].astype(float)
median_sales = fred.get_series_df("MSPUS", observation_start="2021-01-20", observation_end=today).drop(columns={'realtime_start', 'realtime_end'}).rename(columns={"value": "Median Sales Price"})
median_sales['Median Sales Price'] = median_sales['Median Sales Price'].astype(float)
## -- Textual Analysis -- ##
average = mortgage_rate['Mortgage Rate'].mean()
most_recent = mortgage_rate['Mortgage Rate'].iloc[-1]
most_recent_date = pd.to_datetime(mortgage_rate['date'].iloc[-1]).strftime('%B %d, %Y')
before = mortgage_rate['Mortgage Rate'].iloc[0]
house_before_biden = round(median_sales['Median Sales Price'].iloc[0])
house_now = round(median_sales['Median Sales Price'].iloc[-1])

def mortgage_calculator(principal, rate, years):
    r = rate / 100 / 12
    n = years * 12
    payment = principal * r / (1 - (1 + r)**-n)
    return payment
mortgage_before = round(mortgage_calculator(house_before_biden, before, 30))
mortgage_now = round(mortgage_calculator(house_now, most_recent, 30))
text_mortgage_rate = f"""
<ul>
    <li>The 30 year fixed mortgage rate when Biden took office was <b>{before}%</b>.</li>
    <li>The 30 year fixed mortgage rate is now <b>{most_recent}%</b>, a <b>{round((most_recent - before)/before *100)}%</b> increase under Biden.</li>
    <li>Before Biden took office, the median sales price of a house was <b>${house_before_biden:,}</b>, now it is <b>${house_now:,}</b>, a <b>{round((house_now-house_before_biden)/house_before_biden*100)}%</b> increase under Biden</li>
    <li>For a typical mortgage before Biden the monthly payment was <b>${mortgage_before:,}</b>. Now, a typical mortgage payment would be <b>${mortgage_now:,}</b>, an increase of <b>${mortgage_now-mortgage_before:,}</b>.</li>
</ul>
"""
## -- Plot Time -- ##
mortgage_rate['date'] = pd.to_datetime(mortgage_rate['date'])
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"
plt.figure(figsize=(12, 4))
ax = sns.lineplot(x='date', y='Mortgage Rate', data=mortgage_rate, linewidth=3, color=emerald)
plt.title('30 Year Fixed Mortgage Rate Since January 2021', fontsize=18, fontweight='bold', color="black", loc="left")
plt.xlabel('')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.ylabel('Mortgage Rate (%)')
plt.grid(axis='y', alpha=0.3)
sns.despine()
plt.savefig(temp_dir+"/mortgage_rate.png", dpi=600, bbox_inches='tight')


### --- OUR BUDGET VS PRESIDENT BUDGET --- ###
# MARK: OUR BUDGET VS PB
## GET LOCAL DATA ##
df = pd.read_excel("data/gross_debt_gdp.xlsx", header=1)
df = df.iloc[[4,19], 1:12]
df['source'] = ["HBC", "Biden's Budget"]
df_long = df.melt(id_vars='source', var_name='year', value_name='debt_gdp')
df_long['debt_gdp'] = round(df_long['debt_gdp'] * 100)
## FRED Gross Debt to GDP ##
gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
gross_debt_to_gdp = gross_debt_to_gdp.query('date >= "2000"')
gross_debt_to_gdp = gross_debt_to_gdp.rename(columns={'date': 'year', 'value': 'debt_gdp'})
gross_debt_to_gdp['source'] = "Actual"



## COMBINE DATA ##
df = pd.concat([df_long, gross_debt_to_gdp], axis=0)


historic_data_2023 = df[(df['year'] == "2023") & (df['source'] == 'Actual')]['debt_gdp'].values[0] # Get the 'Historic Data's 2023 debt_gdp value
sources = df[df['source'] != 'Actual']['source'].unique() # Get the unique sources other than 'Historic Data'
new_rows = [pd.DataFrame({'year': ["2023"], 'debt_gdp': [historic_data_2023], 'source': [source]}) for source in sources] # For each source, create a new row with the 'Historic Data's 2023 debt_gdp value

df = pd.concat([df] + new_rows, ignore_index=True)
df['year'] = pd.to_numeric(df['year'])
df = df.sort_values(by='year')

## -- Textual Analysis -- ##
earliest_year = df['year'].min()
latest_year = df['year'].max()
earliest = df[df['year'] == earliest_year]['debt_gdp'].values[0].astype(int)
current_year = 2023
current = round(df.query(f"source == 'Actual' & year == {current_year}")["debt_gdp"].values[0])
biden_latest = round(df.query(f"source == \"Biden's Budget\" & year == {latest_year}")['debt_gdp'].values[0])
hbc_latest = round(df.query(f"source == 'HBC' & year == {latest_year}")['debt_gdp'].values[0])

comparison_html = f"""
<ul>
    <li>In {earliest_year}, the gross debt to GDP ratio was <b>{earliest}%</b>.</li>
    <li>In {current_year}, the gross debt to GDP ratio was <b>{current}%</b>.</li>
    <li>Under the President's Budget, the gross debt to GDP ratio will be <b>{biden_latest}%</b> in {latest_year}, an increase of {biden_latest-current} percentage points since {current_year}.</li>
    <li>Under the House Republican Budget, the gross debt to GDP ratio will be <b>{hbc_latest}%</b> in {latest_year}, a decrease of {abs(hbc_latest-current)} percentage points since {current_year}</li>
</ul>
"""
## -- Plot Time -- ##
colors = {'HBC': darker_emerald, 'Biden\'s Budget': gold, 'Actual': jade}
sources = ["HBC", "Biden's Budget", "Actual"] # Get the unique sources
# Set the style and font
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"

# Create a new figure
plt.figure(figsize=(12, 4))

# For each source, add a trace to the figure
for source in sources:
    df_source = df[df['source'] == source]
    plt.fill_between(df_source['year'], df_source['debt_gdp'], color=colors.get(source, 'black'), alpha=0.5, label=source)
    plt.plot(df_source['year'], df_source['debt_gdp'], color=colors.get(source, 'black'))
plt.legend()
# Set the title and labels
plt.title('House Republican Budget vs President Biden\'s Budget', fontsize=18, fontweight='bold', color="black", loc="left")
plt.xlabel('')
plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}%'))
plt.ylabel('Gross Debt as Percentage of GDP')
plt.grid(axis='y', alpha=0.3)
sns.despine()
plt.savefig(temp_dir+"/budget_comparison.png", dpi=600, bbox_inches='tight')



#### ---- RATE OF INCREASE ---- ####
# MARK: RATE OF INCREASE
###NOTE: I make a call to the debt to penny dataset in debt tracker. Not sure if I can consolidate to one call or not. 
## Treasury API ##
# Get debt data
treasury_link = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=10000'
p = requests.get(treasury_link)
data = p.json()
debt_df = pd.DataFrame(data['data'])
# Clean debt data
debt_df['tot_pub_debt_out_amt'] = debt_df['tot_pub_debt_out_amt'].astype(float)
debt_df = debt_df[['record_date','tot_pub_debt_out_amt']]
debt_df["record_date"] = pd.to_datetime(debt_df["record_date"])
debt_df["date_year_ago"] = debt_df["record_date"] - pd.DateOffset(years=1)
# Get the debt from a year ago (or the closest date to a year ago)
debt_df.set_index("record_date", inplace=True) # Set 'record_date' as the index
debt_df["debt_year_ago"] = debt_df["date_year_ago"].apply(lambda x: debt_df["tot_pub_debt_out_amt"].asof(x)) # Use 'asof' to find the closest date
debt_df.reset_index(inplace=True)
# Calculate Rate of Increase
debt_df["year_increase"] = debt_df["tot_pub_debt_out_amt"] - debt_df["debt_year_ago"]
debt_df['second_increase'] = round(debt_df['year_increase'] / 365 / 24 / 60 / 60)
## -- Textual Analysis -- ##
average = round(debt_df['second_increase'].mean())
most_recent = round(debt_df['second_increase'].iloc[-1])
most_recent_date = debt_df['record_date'].iloc[-1].strftime('%B %d, %Y')
earliest = debt_df['second_increase'].iloc[0]
earliest_date = debt_df['record_date'].iloc[0].strftime('%B %d, %Y')
pre_pandemic = round(debt_df[debt_df['record_date']==pd.to_datetime('2020-02-10')]['second_increase'].values[0])
rate_increase_html = f"""
<ul>
    <li>The gross debt is increasing by <b>${most_recent:,}</b> per second.</li>
    <li>Since {earliest_date}, the average increase in the gross debt every second has been <b>${average:,}</b>.</li>
    <li>The current rate is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period and <b>{round((most_recent-pre_pandemic)/pre_pandemic*100)}%</b> above the pre-pandemic rate of ${pre_pandemic:,} per second.</li>
</ul>
"""
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"
plt.figure(figsize=(12, 4))
sns.lineplot(x='record_date', y='second_increase', data=debt_df, linewidth=3, color=emerald)
plt.title('Rate of Debt Accumulation Since 1994', fontsize=18, fontweight='bold', color="black", loc="left")
plt.xlabel('')
plt.gca().yaxis.set_major_formatter('${x:,.0f}')
plt.ylabel('Debt Increase per Second')
plt.grid(axis='y', alpha=0.3)
sns.despine()
plt.savefig(temp_dir+"/debt_increase.png", dpi=600, bbox_inches='tight')


#### ---- CBO Projections ---- ####
# MARK: CBO PROJECTIONS
### FRED Gross Debt to GDP ###
gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
gross_debt_to_gdp = gross_debt_to_gdp.query('date > "1944"')

### CBO LTBO GROSS DEBT TO GDP ###
cbo_ltbo = pd.read_excel("data/51119-2024-03-LTBO-budget.xlsx", sheet_name=1, header=9)
cbo_ltbo = cbo_ltbo[["Fiscal year", "Gross federal debte"]].rename(columns={"Fiscal year": "date", "Gross federal debte": "value"}).dropna()
cbo_ltbo['value'] = round(cbo_ltbo['value'])
### MERGE THE TWO DATASETS ###
combined = pd.concat([gross_debt_to_gdp, cbo_ltbo], axis=0)
combined['date'] = combined['date'].astype(str)
## -- Textual Analysis -- ##
current_year = 2023
earliest_year = combined['date'].iloc[0]
latest_year = combined['date'].iloc[-1]
latest = round(combined[combined['date'] == latest_year]['value'].values[0])
peak = round(combined['value'].max())
peak_year = combined[combined['value'] == peak]['date'].values[0]
average = round(combined.query(f"date < {current_year}")['value'].mean())
random_html = f"""
<ul>
    <li> The gross debt to GDP ratio peaked at {peak}% in {peak_year}.</li>
    <li> The gross debt to GDP ratio averaged {average}% from {earliest_year} to {current_year}.</li>
    <li> Under current law, CBO projects our debt to GDP will reach <b>{latest}%</b> in {latest_year}. This is <b>{round((latest-average)/average * 100)}</b> above the historical average since {earliest_year}.</li>
</ul>
"""
## -- Plot Time -- ##
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"
plt.figure(figsize=(12, 4))
plt.fill_between(combined['date'], combined['value'], color="#84AE95", alpha=0.8)
plt.title("Gross Debt to GDP, Historical and Projected", fontsize=18, fontweight='bold', color="black", loc="left")
plt.xticks(combined['date'][::10])
plt.xlabel('Gross Debt to GDP')
plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}%'))
sns.despine()
# Add the annotations
actual_value_2023 = round(combined.loc[combined['date'] == "2023", 'value'].values[0])
projected_value_2054 = round(combined.loc[combined['date'] == "2054", 'value'].values[0])
plt.annotate(f'Actual: {actual_value_2023}% in 2023', ("2023", actual_value_2023), textcoords="offset points", xytext=(-20,20), ha='center', color='black', arrowprops=dict(arrowstyle='->', color='black'))
plt.annotate(f'Projected: {projected_value_2054}% in 2054', ("2054", projected_value_2054), textcoords="offset points", xytext=(-40,10), ha='center', color='black', arrowprops=dict(arrowstyle='->', color='black'))
plt.savefig(temp_dir+"/cbo_projections.png", dpi=600, bbox_inches='tight')

#### ---- GDP ADDED VS DEBT ADDED ---- ####
# MARK: GDP VS DEBT
## -- FRED GDP -- ##
start = "2022-01-01"
today_quarter = quarter_dict[int(today[5:7])]
gdp = fred.get_series_df("GDP", observation_start=start, observation_end=today).rename(columns={"value": "GDP"}).drop(columns=['realtime_start', 'realtime_end'])
gdp['quarter'] = gdp['date'].apply(lambda x: f"{quarter_dict[int(x[5:7])]}")
gdp['year'] = gdp['date'].apply(lambda x: x[:4])
gdp["GDP"] = gdp["GDP"].astype(float) * 1e9
gdp = gdp.query("quarter == 'Q4'").drop(columns=['date', 'quarter'])
## -- FRED Debt -- ##
debt = fred.get_series_df("GFDEBTN", observation_start=start, observation_end=today).rename(columns={"value": "Debt"}).drop(columns=['realtime_start', 'realtime_end'])
debt['quarter'] = debt['date'].apply(lambda x: f"{quarter_dict[int(x[5:7])]}")
debt['year'] = debt['date'].apply(lambda x: x[:4])
debt["Debt"] = debt["Debt"].astype(float) * 1e6
debt = debt.query("quarter == 'Q4'").drop(columns=['date', 'quarter'])

## -- Textual Analysis -- ##
gdp_increase = gdp['GDP'].iloc[-1] - gdp['GDP'].iloc[0]
gdp_day = gdp_increase / 365
debt_increase = debt['Debt'].iloc[-1] - debt['Debt'].iloc[0]
debt_day = debt_increase / 365
text_gdp_debt = f"""
<ul>
    <li>In 2023, GDP grew by <b>${gdp_increase/1e12:.2f}</b> trillion and gross debt grew by <b>${debt_increase/1e12:.2f}</b> trillion.</li>
    <li>This equates to a <b>${gdp_day/1e9:,.2f} billion</b> increase in GDP every day and <b>${debt_day/1e9:,.2f} billion </b> increase in debt every day in 2023.</li>
    <li>In 2023, the growth in the gross debt was <b>{round((debt_increase/gdp_increase)*100)}%</b> higher than the growth in GDP.</li>
</ul>
"""
## -- Chart Time -- ##
# Data
categories = ['GDP Increase', 'Debt Increase']
values = [gdp_increase/1e12, debt_increase/1e12]
# Plot
sns.set_style("white")
plt.rcParams["font.family"] = "Playfair Display"
plt.figure(figsize=(12, 4))
# Create horizontal bar chart
bars = plt.barh(categories, values, color=[gold, emerald])
# Add data values inside the bars
for bar in bars:
    width = bar.get_width()
    plt.text(width - 0.07, bar.get_y() + bar.get_height() / 2, f'${width:.2f} trillion', ha='right', va='center', color='white', fontweight='bold', fontsize=14)

plt.title('GDP Added vs Debt Added in 2023', fontsize=18, fontweight='bold', color="black", loc="left")
plt.xlabel('')
plt.xticks([])
sns.despine(left=True, bottom=True)
plt.savefig(temp_dir+"/gdp_debt.png", dpi=600, bbox_inches='tight')

print("Cool Debt Metrics script complete.")