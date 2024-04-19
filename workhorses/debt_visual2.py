#### COMPARE OUR BUDGET TO THE PRESIDENT'S BUDGET WITH HISTORIC DATA AS BASE ####
import pandas as pd
import plotly.graph_objects as go
from full_fred.fred import Fred
from datetime import date
import streamlit as st
import os
os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
today = date.today().strftime("%Y-%m-%d")

### GET LOCAL DATA ###
df = pd.read_excel("data/gross_debt_gdp.xlsx", header=1)
df = df.iloc[[4,19], 1:11]
df['source'] = ["HBC", "Biden's Budget"]
df_long = df.melt(id_vars='source', var_name='year', value_name='debt_gdp')
df_long['debt_gdp'] = round(df_long['debt_gdp'] * 100)
### FRED Gross Debt to GDP ###
gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
gross_debt_to_gdp = gross_debt_to_gdp.query('date > "2006"')
gross_debt_to_gdp = gross_debt_to_gdp.rename(columns={'date': 'year', 'value': 'debt_gdp'})
gross_debt_to_gdp['source'] = "Actual"

### COMBINE DATA ###
df = pd.concat([df_long, gross_debt_to_gdp], axis=0)


historic_data_2023 = df[(df['year'] == "2023") & (df['source'] == 'Actual')]['debt_gdp'].values[0] # Get the 'Historic Data's 2023 debt_gdp value
sources = df[df['source'] != 'Actual']['source'].unique() # Get the unique sources other than 'Historic Data'
new_rows = [pd.DataFrame({'year': ["2023"], 'debt_gdp': [historic_data_2023], 'source': [source]}) for source in sources] # For each source, create a new row with the 'Historic Data's 2023 debt_gdp value

df = pd.concat([df] + new_rows, ignore_index=True)
df['year'] = pd.to_numeric(df['year'])
df = df.sort_values(by='year')

### PLOT ###


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
    title={'text': "<b>Gross Debt to GDP, HBC Budget Resolution vs President's Budget</b>",'font': dict(size=26, color="#000000", family="Montserrat")},
    yaxis=dict(range=[0, max(df['debt_gdp'])]),
    legend = dict(font=dict(family="Montserrat", color="black", size=13)),
    width = 900, height = 500
)

fig.update_xaxes(showgrid=False, tickfont = dict(family="Montserrat"))
fig.update_yaxes(ticksuffix="%", tickfont = dict(family="Montserrat"))