import streamlit as st
import plotly.express as px

from workhorses import cool_debt_metrics as cdm 
from workhorses import debt_tracker as dt
st.title("Testing Writing Image")


### --- create images from plotly --- ###

d_to_a_image = cdm.debt_to_assets_plotly.write_image("debt_to_assets.png")
d_to_w_image = cdm.debt_to_wages_plotly.write_image("debt_to_wages.png")
mortgage_image = cdm.mortgage_plotly.write_image("mortgage_rate.png")
us_vs_biden_image = cdm.us_vs_biden_plotly.write_image("our_vs_president.png")
rate_increase_image = cdm.rate_increase_plotly.write_image("rate_increase.png")
cbo_image = cdm.cbo_proj_plotly.write_image("cbo.png")
debt_vs_gdp_image = cdm.debt_vs_gdp_plotly.write_image("debt_vs_gdp.png")


### --- assemble html --- ###

basic_debt_html = f"""
<div class="container">
<div class="content">
    <h2>Current Debt</h2>
    <p>The gross national debt is currently <strong>${dt.current_debt_rounded:,} trillion</strong>. This equates to:</p>
    <ul>
        <li><strong>${dt.debt_per_person:,}</strong> per person</li>
        <li><strong>${dt.debt_per_household:,}</strong> per household</li>
        <li><strong>${dt.debt_per_child:,}</strong> per child</li>
    </ul>

    <h2>Debt Accumulation under President Biden</h2>
    <p>When President Biden took office total gross debt was <strong>${dt.biden_start_debt_rounded:,} trillion</strong>, meaning he has increased the national debt by <strong>${dt.biden_debt_rounded:,} trillion</strong>. This equates to:</p>
    <ul>
        <li><strong>${dt.biden_debt_per_person:,}</strong> more debt per person</li>
        <li><strong>${dt.biden_debt_per_household:,}</strong> more debt per household</li>
        <li><strong>${dt.biden_debt_per_child:,}</strong> more debt per child</li>
    </ul>
    <p>The rate of debt accumulation during the Biden Administration has equaled:</p>
    <ul>
        <li><strong>${dt.biden_debt_per_day_rounded:,} billion</strong> in new debt per day</li>
        <li><strong>${dt.biden_debt_per_hour:,} million</strong> in new debt per hour</li>
        <li><strong>${dt.biden_debt_per_min:,} million</strong> in new debt per minute</li>
        <li><strong>${dt.biden_debt_per_sec:,}</strong> in new debt per second</li>
    </ul>

    <h2>Debt Accumulation in Past Year</h2>
    <p>The debt one year ago was <strong>${dt.debt_year_ago_rounded:,} trillion</strong>, meaning that the debt has increased by <strong>${dt.debt_increase_from_year_ago_rounded:,} trillion</strong> over the past 12 months. This rate of increase equates to:</p>
    <ul>
        <li><strong>${dt.last_year_debt_per_day_rounded:,} billion</strong> in new debt per day</li>
        <li><strong>${dt.last_year_debt_per_hour:,} million</strong> in new debt per hour</li>
        <li><strong>${dt.last_year_debt_per_min:,} million</strong> in new debt per minute</li>
        <li><strong>${dt.last_year_debt_per_sec:,}</strong> in new debt per second</li>
    </ul>
</div>
</div>
"""


html = f"""
<!DOCTYPE html>
<html>
<head>
    <center>
        <img src="data/HBR_Logo_Primary.png" width="500" align = "middle">
    </center> 
    <title>Debt Tracker</title>
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
<br> </br>
<div class="header">
    <h1>Debt Tracker</h1>
</div>
{basic_debt_html}
    <div class="header">
        <h1>Understanding the Debt</h1>
    </div>
    <div class="container">
        <div class="content">
            <h2>Debt to Federal Assets</h2>
            <p>{cdm.text_debt_to_assets}</p>
            {d_to_a_image}           
            <h2>Debt to Wages</h2>
            <p>{cdm.text_debt_to_wages}</p>
            <img src="debt_to_wages.png" width="500" align = "left">
            <h2>Mortgage Rates</h2>
            <p>{cdm.text_mortgage_rate}</p>
            <img src="mortgage_rate.png" width="500" align = "left">
            <h2>Our Budget vs President's Budget</h2>
            <p>{cdm.comparison_html}</p>
            <img src="our_vs_president.png" width="500" align = "left">
            <h2>Rate of Increase</h2>
            <p>{cdm.rate_increase_html}</p>
            <img src="rate_increase.png" width="500" align = "left">
            <h2>CBO Projections</h2>
            <p>{cdm.random_html}</p>
            <img src="cbo.png" width="500" align = "left">
            <h2>GDP Growth vs Debt Growth</h2>
            <p>{cdm.text_gdp_debt}</p>
            <img src="debt_vs_gdp.png" width="500" align = "left">
        </div>
    </div>
</body>
</html>
"""

st.markdown(html, unsafe_allow_html=True)