#### PRODUCE THE HTML NEEDED FOR THE COOL DEBT METRICS ####
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from full_fred.fred import Fred
from datetime import date
import requests 
import json
import streamlit as st
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
today = date.today().strftime("%Y-%m-%d")


### DEBT TO FEDERAL ASSETS ###
## get data ##
startdate = "1966-01-01"
financial_assets = fred.get_series_df("FGTFASQ027S", observation_start=startdate, observation_end=today).rename(columns={"value": "Financial Assets"}).drop(columns=["realtime_start", "realtime_end"])
total_debt = fred.get_series_df("GFDEBTN", observation_start=startdate, observation_end=today).rename(columns={"value": "Total Debt"}).drop(columns=["realtime_start", "realtime_end"])
debt_to_assets = total_debt.join(financial_assets, how="inner",  lsuffix='_total_debt', rsuffix='_financial_assets')
debt_to_assets[["Total Debt", "Financial Assets"]] = debt_to_assets[["Total Debt", "Financial Assets"]].apply(pd.to_numeric)
debt_to_assets['debt_to_assets'] = debt_to_assets['Total Debt'] / debt_to_assets['Financial Assets']
debt_to_assets = debt_to_assets[['date_total_debt', "Total Debt", "Financial Assets", "debt_to_assets"]]

## Textual Analysis ##
average = debt_to_assets['debt_to_assets'].mean()
most_recent = debt_to_assets['debt_to_assets'].iloc[-1]
most_recent_date = debt_to_assets['date_total_debt'].iloc[-1]
peak = debt_to_assets['debt_to_assets'].max()
peak_date = debt_to_assets['date_total_debt'][debt_to_assets['debt_to_assets'] == peak].values[0]


## DEBT TO ASSETS PLOT ##
fig = px.line(debt_to_assets, x='date_total_debt', y='debt_to_assets', title='Debt to Federal Assets', labels={'date_total_debt':'Date', 'debt_to_assets':'Debt to Assets'})
fig.update_layout(template='plotly_white', title='<b>Ratio of Gross Debt to Federal Assets Since 1966</b>', titlefont=dict(size=24, family="Montserrat", color="black"))                                                                                                                        
fig.update_xaxes(title_text="", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_yaxes(title_text="Debt to Assets", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_traces(line=dict(width=3.5, color="#004647"), hovertemplate='<b>%{x}</b><br>%{y}')

## -- HTML -- ##
fig_debt_to_assets = fig.to_html(full_html=False)
text_debt_to_assets = f"""
<ul>
    <li>Since 1966, our debt to asset ratio has averaged {round(average, 2)}.</li>
    <li>As of {most_recent_date}, our debt to asset ratio is {round(most_recent, 2)}.</li>
    <li>This is {round((most_recent - average)/average *100)}% above the average for this period.</li>
    <li>The debt to assets ratio peaked in {peak_date} at {round(peak, 2)}.</li>
</ul>
"""
### RATIO OF DEBT TO TOTAL WAGES ###
## BLS api ##
BLS_API_KEY = "c7235bf234c449e2a58b4dd227ac9b81"
headers = {'Content-type': 'application/json'}

startyear = "2004"
endyear = "2023"

def bls_df(series, startyear, endyear):
    data = json.dumps({"seriesid": series, "startyear": startyear, "endyear": endyear, "catalog": True, "registrationkey": BLS_API_KEY, "annualaverage":True})
    p = requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=data, headers=headers)
    json_data = json.loads(p.text)
    #print(json_data)
    data = {"series_id": [], "year": [], "period": [], "value": [], "footnotes": []}
    for series in json_data['Results']['series']:
        #print(series)
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

## FRED DEBT per Quarter ###
annual_debt = fred.get_series_df("GFDEBTN", observation_start="2000-01-01", observation_end=today, frequency="a").drop(columns=['realtime_start', 'realtime_end']).rename(columns={"value": "Total Debt"})
annual_debt['year'] = annual_debt['date'].str[:4]
annual_debt['Total Debt'] = annual_debt['Total Debt'].astype(float) * 1e6
## Retreieve and Clean BLS Data ##
quarterly_wages = bls_df(["ENUUS00030010"], startyear, endyear)
quarterly_wages['value'] = quarterly_wages['value'].astype(float) * 1000
quarterly_wages["quarter-yr"] = quarterly_wages["period"] + "-" + quarterly_wages["year"]
quarterly_wages = quarterly_wages.rename(columns={"value": "Wages"})
annual_wages = quarterly_wages.query("period == 'Q05'")
## Merge Data and Calculate Ratio ##
debt_to_wage = annual_debt.merge(annual_wages, on="year", how="inner")
debt_to_wage['debt_to_wages'] = debt_to_wage['Total Debt'] / debt_to_wage['Wages']
debt_to_wage = debt_to_wage[['year', 'Total Debt', 'Wages', 'debt_to_wages']]
## Textual Analysis ##
average = debt_to_wage['debt_to_wages'].mean()
most_recent = debt_to_wage['debt_to_wages'].iloc[-1]
most_recent_year = debt_to_wage['year'].iloc[-1]
earliest_year = debt_to_wage['year'].iloc[0]
earliest = debt_to_wage['debt_to_wages'].iloc[0]
peak = debt_to_wage['debt_to_wages'].max()
peak_year = debt_to_wage['year'][debt_to_wage['debt_to_wages'] == peak].values[0]

## Plot Time ##
fig = px.line(debt_to_wage, x='year', y='debt_to_wages', title='Debt to Wages', labels={'year':'Year', 'debt_to_wages':'Debt to Wages'})
fig.update_layout(template='plotly_white', title='<b>Ratio of Gross Debt to Total Wages Since 2004</b>', titlefont=dict(size=24, family="Montserrat", color="black"))
fig.update_xaxes(title_text="", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_yaxes(title_text="Debt to Wages", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_traces(line=dict(width=3.5, color="#004647"), hovertemplate='<b>%{x}</b><br>%{y}')


## -- HTML -- ##
fig_debt_to_wages = fig.to_html(full_html=False)
text_debt_to_wages = f"In {earliest_year}, our debt to wage ratio was {round(earliest, 2)}. As of {most_recent_year}, our debt to wage ratio is {round(most_recent, 2)}. This is a {round((most_recent - earliest)/earliest *100)}% increase. Since {earliest_year}, our debt to wage ratio has averaged {round(average, 2)}. This is {round((most_recent - average)/average *100)}% above the average for this period. The debt to wage ratio peaked in {peak_year} at {round(peak, 2)}."
#add new lines
text_debt_to_wages = f"In {earliest_year}, our debt to wage ratio was {round(earliest, 2)}.\nAs of {most_recent_year}, our debt to wage ratio is {round(most_recent, 2)}.\nThis is a {round((most_recent - earliest)/earliest *100)}% increase.\nSince {earliest_year}, our debt to wage ratio has averaged {round(average, 2)}.\nThis is {round((most_recent - average)/average *100)}% above the average for this period.\nThe debt to wage ratio peaked in {peak_year} at {round(peak, 2)}."
#html version
text_debt_to_wages = f"""
<ul>
    <li>In {earliest_year}, our debt to wage ratio was {round(earliest, 2)}.</li>
    <li>As of {most_recent_year}, our debt to wage ratio is {round(most_recent, 2)}, a {round((most_recent - earliest)/earliest *100)}% increase since {earliest_year}.</li>
    <li>Since {earliest_year}, our debt to wage ratio has averaged {round(average, 2)}. Our current debt to wage ratio is {round((most_recent - average)/average *100)}% above the average for this period.</li>
    <li>The debt to wage ratio peaked in {peak_year} at {round(peak, 2)}.</li>
</ul>
"""
### --- MORTGAGE RATES SINCE JAN 2021 --- ###
## -- FRED Data -- ##
mortgage_rate = fred.get_series_df("MORTGAGE30US", observation_start="2021-01-20", observation_end=today).drop(columns={'realtime_start', 'realtime_end'}).rename(columns={"value": "Mortgage Rate"})
mortgage_rate['Mortgage Rate'] = mortgage_rate['Mortgage Rate'].astype(float)
## -- Textual Analysis -- ##
average = mortgage_rate['Mortgage Rate'].mean()
most_recent = mortgage_rate['Mortgage Rate'].iloc[-1]
most_recent_date = mortgage_rate['date'].iloc[-1]
peak = mortgage_rate['Mortgage Rate'].max()
peak_date = mortgage_rate['date'][mortgage_rate['Mortgage Rate'] == peak].values[0]
before = mortgage_rate['Mortgage Rate'].iloc[0]

def mortgage_calculator(principal, rate, years):
    r = rate / 100 / 12
    n = years * 12
    payment = principal * r / (1 - (1 + r)**-n)
    return payment

## -- Plot Time -- ##
fig = px.line(mortgage_rate, x='date', y='Mortgage Rate', title='30 Year Fixed Mortgage Rate', labels={'date':'Date', 'Mortgage Rate':'Rate'})
fig.update_layout(template='plotly_white', title='<b>30 Year Fixed Mortgage Rate Since January 2021</b>', titlefont=dict(size=24, family="Montserrat", color="black"))
fig.update_xaxes(title_text="", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_yaxes(title_text="Rate (%)", tickfont=dict(size=14, family="Montserrat", color="black"))
fig.update_traces(line=dict(width=3.5, color="#004647"), hovertemplate='<b>%{x}</b><br>%{y}')


## -- HTML -- ##
fig_mortgage_rate = fig.to_html(full_html=True)
#html version
text_mortgage_rate = f"""
<ul>
    <li>The 30 year fixed mortgage rate when Biden took office was {before}%.</li>
    <li>As of {most_recent_date}, the 30 year fixed mortgage rate is now {most_recent}%.</li>
    <li>This is {round((most_recent - before)/before *100)}% above the rate when Biden took office.</li>
    <li>The 30 year fixed mortgage rate peaked on {peak_date} at {round(peak, 2)}%.</li>
    <li>For a $380,000 mortgage the monthly payment before Biden took office would have been ${round(mortgage_calculator(380000, before, 30))}.</li>
    <li>Now, the monthly payment would be ${round(mortgage_calculator(380000, most_recent, 30))}.</li>
</ul>
"""
### --- OUR BUDGET VS PRESIDENT BUDGET --- ###
## GET LOCAL DATA ##
df = pd.read_excel("data/gross_debt_gdp.xlsx", header=1)
df = df.iloc[[4,19], 1:11]
df['source'] = ["HBC", "Biden's Budget"]
df_long = df.melt(id_vars='source', var_name='year', value_name='debt_gdp')
df_long['debt_gdp'] = round(df_long['debt_gdp'] * 100)
## FRED Gross Debt to GDP ##
gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
gross_debt_to_gdp = gross_debt_to_gdp.query('date > "2006"')
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
current = df.query(f"source == 'Actual' & year == {current_year}")["debt_gdp"].values[0].astype(int)
biden_latest = df.query(f"source == \"Biden's Budget\" & year == {latest_year}")['debt_gdp'].values[0].astype(int)
hbc_latest = df.query(f"source == 'HBC' & year == {latest_year}")['debt_gdp'].values[0].astype(int)

comparison_html = f"""
<ul>
    <li> In {earliest_year}, our debt to GDP ratio was {earliest}%.</li>
    <li>As of 2023, our debt to GDP ratio is {current}%.</li>
    <li>Under the President's Budget, our debt to GDP ratio will be {biden_latest}% in {latest_year}, an increase of {biden_latest-current} percentage points since {current_year}.</li>
    <li>Under the House Republican Budget, our debt to GDP ratio will be {hbc_latest}% in {latest_year}, a decrease of {abs(hbc_latest-current)} percentage points since {current_year}</li>
</ul>
"""

## -- Plot Time -- ##
colors = {'HBC': '#84AE95', 'Biden\'s Budget': '#e88489', 'Actual': '#b2dbc2'}
sources = ["HBC", "Biden's Budget", "Actual"] # Get the unique sources
fig = go.Figure() # Create a new figure

# For each source, add a trace to the figure
for source in sources:
    df_source = df[df['source'] == source]
    if source == 'HBC':
        fig.add_trace(go.Scatter(x=df_source['year'], y=df_source['debt_gdp'], fill='tozeroy', mode="lines", name=source, line=dict(color=colors.get(source, 'black'))))#colors['Our Budget']))
    elif source == "Biden's Budget":
        fig.add_trace(go.Scatter(x=df_source['year'], y=df_source['debt_gdp'], fill='tonexty', mode="lines", name=source, line=dict(color=colors.get(source, 'black'))))
    else:
        fig.add_trace(go.Scatter(x=df_source['year'], y=df_source['debt_gdp'], fill='tozeroy', mode="lines", name=source, line=dict(color=colors.get(source, 'black'))))

# Update the layout
fig.update_layout(
    template='plotly_white', 
    hovermode="x unified",
    title={'text': "<b>Gross Debt to GDP, HBC Budget Resolution vs President's Budget</b>",'font': dict(size=24, color="black", family="Montserrat")},
    yaxis=dict(range=[0, max(df['debt_gdp'])]),
    legend = dict(font=dict(family="Montserrat", color="black", size=13))
)

fig.update_xaxes(showgrid=False, tickfont = dict(family="Montserrat"))
fig.update_yaxes(ticksuffix="%", tickfont = dict(family="Montserrat"))


## -- HTML -- ##
fig_debt_gdp = fig.to_html(full_html=False)


### -- RATE OF INCREASE -- ###
## Treasury API ##
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
## -- Textual Analysis -- ##
average = round(debt_df['second_increase'].mean())
most_recent = round(debt_df['second_increase'].iloc[-1])
most_recent_date = debt_df['record_date'].iloc[-1].strftime('%B %d, %Y')
earliest = debt_df['second_increase'].iloc[0]
earliest_date = debt_df['record_date'].iloc[0].strftime('%B %d, %Y')
peak = round(debt_df['second_increase'].max())
peak_date = pd.to_datetime(debt_df['record_date'][debt_df['second_increase'] == peak].values[0]).strftime('%B %d, %Y')
pre_pandemic = int(debt_df.query("record_date == '2020-02-10'")['second_increase'].values[0])
rate_increase_html = f"""
<ul>
    <li>Since {earliest_date}, the average increase in our debt every second has been ${average:,}.</li>
    <li>As of {most_recent_date}, our debt is increasing by ${most_recent:,} per second.</li>
    <li>This is {round((most_recent - average)/average *100)}% above the average for this period and {round((most_recent-pre_pandemic)/pre_pandemic*100)}% above the pre-pandemic rate of ${pre_pandemic:,} per second.</li>
    <li>The debt increase peaked on {peak_date} at ${peak:,} per second.</li>
</ul>
"""

## -- Plot Time -- ##
fig = px.line(debt_df, x='record_date', y='second_increase')
fig.update_xaxes(title_text='',showgrid=False, tickfont=dict(size=12, family="Montserrat"))
fig.update_yaxes(title_text='<b>Debt Increase per Second</b>', titlefont=dict(family="Montserrat", size=14), tickprefix="$", tickfont=dict(size=12, family="Montserrat"))
fig.update_layout(template='plotly_white', title='<b>Rate of Debt Accumulation Since 1994</b>', titlefont=dict(size=24, family="Montserrat", color="black"))
fig.update_traces(line=dict(width=3, color="#004647"), hovertemplate="Date: %{x}<br>Increase per second: %{y}")
## -- HTML -- ##
fig_debt_increase = fig.to_html(full_html=False)


### --- CBO Projections --- ###
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

## -- Textual Analysis -- ##
earliest_year = combined['date'].iloc[0]
latest_year = combined['date'].iloc[-1]
latest = combined[combined['date'] == latest_year]['value'].values[0]
random_html = f"""
<ul>
    <li> Under current law, CBO projects our debt to GDP will reach {latest} in {latest_year} </li>
</ul>
"""

## -- Plot Time -- ##
fig = px.area(combined, x='date', y='value', title='Gross Debt to GDP Since 1945')

fig.update_layout(
    template='plotly_white', 
    margin = dict(b=0), 
    hovermode="x unified",
    title={'text': "<b>Gross Debt to GDP, 1945 to 2054</b>",'font': dict(size=24, color="#000000", family="Playfair Display, serif")}
)

fig.update_xaxes(
    title_text='', 
    showgrid=False, 
    tickvals=list(range(1950, 2050, 10)), 
    tickfont=dict(
        family='PLayfair Display, serif', size=14,color='#000000'),
    tickformat = "<b>%{value}</b>"
)

fig.update_yaxes(
    title_text='', 
    showgrid=True, 
    tickformat = "<b>.0f</b>", 
    ticksuffix="%",
    tickfont=dict(family='PLayfair Display, serif',size=14, color='#000000')
)

fig.add_annotation(
    x=78, y=140, # this is the point to which the text refers
    text="<b>Actual: 121% in 2023</b>", # this is the text
    showarrow=True, # it will show an arrow from the text to the point
    font=dict(family="Playfair Display, serif", size=14, color="#000000"),
    arrowhead=2,    arrowsize=1,    arrowwidth=2,    arrowcolor="#636363",    ax=20,    ay=-30,
)

fig.add_annotation(
    x=106, y=190,
    text="<b>Projected: 179% in 2054</b>",
    showarrow=True,
    font=dict(family="Playfair Display, serif",size=14,color="#000000"),
    arrowhead=2,    arrowsize=1,    arrowwidth=2,    arrowcolor="#636363",    ax=-50,    ay=-20,
)

fig.update_traces(fillcolor="#84AE95", line = dict(color="#84AE95"), hovertemplate="%{y}")

## -- HTML -- ##
fig_random = fig.to_html(full_html=False)



### --- HTML --- ###
html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Debt Ideas</title>
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
            width: 100%;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Debt Metrics</h1>
    </div>
    <div class="container">
        <div class="content">
            <h2>Debt to Federal Assets</h2>
            <p>{text_debt_to_assets}</p>
            {fig_debt_to_assets}
            <h2>Debt to Wages</h2>
            <p>{text_debt_to_wages}</p>
            {fig_debt_to_wages}
            <h2>Mortgage Rates</h2>
            <p>{text_mortgage_rate}</p>
            {fig_mortgage_rate}
            <h2>Our Budget vs President's Budget</h2>
            <p>{comparison_html}</p>
            {fig_debt_gdp}
            <h2>Rate of Increase</h2>
            <p>{rate_increase_html}</p>
            {fig_debt_increase}
            <h2>CBO Projections</h2>
            <p>{random_html}</p>
            {fig_random}
        </div>
    </div>
</body>
</html>
"""

