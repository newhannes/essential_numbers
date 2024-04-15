#### VISUALIZE GROSS DEBT TO GDP HISTORICALLY ####
import pandas as pd
import plotly.express as px
#import plotly.graph_objects as go
import matplotlib.pyplot as plt
from full_fred.fred import Fred
from datetime import date
import streamlit as st

FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
today = date.today().strftime("%Y-%m-%d")

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

### CHART TIME ###
plt.figure(figsize=(8, 6))
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
    tickvals=list(range(1950, 2051, 10)), 
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
    arrowhead=2,    arrowsize=1,    arrowwidth=2,    arrowcolor="#000000",    ax=20,    ay=-30,
)

fig.add_annotation(
    x=106, y=190,
    text="<b>Projected: 179% in 2054</b>",
    showarrow=True,
    font=dict(family="Playfair Display, serif",size=14,color="#000000"),
    arrowhead=2,    arrowsize=1,    arrowwidth=2,    arrowcolor="#000000",    ax=-50,    ay=-20,
)

fig.update_traces(fillcolor="#84AE95", line = dict(color="#84AE95"), hovertemplate="%{y}")