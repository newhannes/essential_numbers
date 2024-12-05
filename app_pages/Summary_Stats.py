import streamlit as st
import pdfkit
import pandas as pd
from datetime import datetime
from workhorses.debt_tracker import debt_tracker_main
from workhorses.summary_data_functions import get_inflation_data, get_labor_data, get_interest_data, get_gas_oil_data

# Get dates
CURRENT_YEAR = datetime.now().year
CURRENT_DATE = datetime.now()
CURRENT_DATE_STRING = CURRENT_DATE.strftime('%Y-%m-%d')
# API Key
FRED_API_KEY = st.secrets["FRED_API_KEY"]
# Helper Functions 
def ordinaltg(n):
  return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


#### ==== Fetch Data ==== #### 
debt_tracker = debt_tracker_main()
inflation_data = get_inflation_data()
labor_data = get_labor_data(inflation_data["cpi_df"])
interest_rates_data = get_interest_data()
gas_oil_data = get_gas_oil_data()

#### ==== Unpack Data ==== ####
for data_dictionary in [debt_tracker, inflation_data, labor_data, interest_rates_data, gas_oil_data]:
    for key, value in data_dictionary.items():
        if not isinstance(value, pd.DataFrame):
            if isinstance(value, str):
                value = f'"{value}"'
            try:    
                exec(f"{key} = {value}")
            except(SyntaxError):
                print(f"Error unpacking {key} with value {value}")

#### ==== HTML and PDF Creation ==== ####
image_path = "/mount/src/essential_numbers/inputs/HBR_Logo_Primary.png"
style_html = f'''
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
            '''
html = f'''
    {style_html}
            <div class="header">
                <h1>Data Summary Report as of {CURRENT_DATE.strftime("%B")} {ordinaltg(CURRENT_DATE.day)}, {CURRENT_DATE.year}</h1>
            </div>
            <div class="container">
                <div class="content">
            <h2><b>Inflation</b></h2>
            <p>Year-over-year CPI inflation as of {cpi_month_year} is <b>{cpi_current} percent</b></p>
            <ul>
                <li>Since January 2021, prices have increased by <b>{biden_inflation} percent</b></li> 
                    <ul>
                        <li>This means that the average family of four is paying an additional <b>${kole_inc:,} per year or ${mon_kole_inc:,} per month</b> to purchase the same goods and services as in January 2021.</li>
                    </ul>
                <li>Since President Biden took office, <b>food</b> prices are up <b>{food_biden} percent</b>;
                    <b>energy</b> prices have risen <b>{energy_biden} percent</b>; and 
                    <b>housing</b> prices are up <b>{housing_biden} percent</b></li>                                     
            </ul>
            <h2><b>Job Market and Wages</b></h2>
            <p>The labor market has not returned to its pre-Covid strength. For example:</p>
            <ul>
                <li>Relative to when President Biden took office in January 2021, real earnings are down <b>{real_earnings_biden} percent</b></li>
                <li>The {current_lfpr_date} labor force participation rate is <b>{current_lfpr} percent</b>, equating to a total labor force of <b>{labor_level} million</b> Americans</li>
                    <ul>
                        <li>This is <b>{abs(lfpr_change)} {'percentage points higher' if lfpr_change > 0 else ('percentage points higher' if lfpr_change == 0 else 'percentage points lower')}</b> than the labor force participation rate just prior to the COVID-19 pandemic: <b>63.3 percent in February 2020</b></li>
                        <li>Outside of the pandemic, this is the lowest level since <b>{lowest_before_pandemic_date} which was {lowest_before_pandemic_val}</b>
                        <li>{'This equates to approximately' if lfpr_change < 0 else ''} <b>{adjusted_pop if lfpr_change < 0 else ''} {'million fewer Americans in the labor force' if lfpr_change < 0 else ''}</b>{' when adjusting for population gains' if lfpr_change < 0 else ''}</li>
                    </ul>
            </ul>
            <h2><b>Interest Rates</b></h2>
            <p>Due to Biden's inflation crisis, interest rates have risen dramatically:</p>
            <ul>
                <li>When President Biden took office, the Federal Funds Rate was between <b>0 and 0.25 percent</b>. Now, the Federal Funds Rate sits between <b>{fed_target_lower_now} and {fed_target_upper_now} percent</b>
                <li>The 10-year treasury yield in January 2021 was <b>{treasury_10_biden_start} percent</b>, now the 10-year yield is <b>{treasury_10_now} percent</b></li>
            </ul>
            <h2><b>Oil and Gas Prices</b></h2>
            <p>President Biden's disastrous energy policy has caused oil and gas prices to skyrocket:</p>
            <ul>         
                <li>When President Trump was in office, the average for a gallon of gas was <b>${gas_trump_average}</b>, and the average price per barrel of oil was <b>$53.11</b></li>
                <li>Now, a gallon of gas is <b>${gas_now}</b> and a barrel of WTI crude oil is <b>${oil_now}</b></li>
            </ul>
            <h2><b>Debt Tracker</b></h2>
            <p>The gross national debt is currently <b>${current_debt_rounded} trillion</b>. This equates to:</p>
            <ul>
                <li><b>${debt_per_person:,}</b> per person in the U.S.</li>
                <li><b>${debt_per_household:,}</b> per household in the U.S.</li>
                <li><b>${debt_per_child:,}</b> per child in the U.S.</li>
            </ul>
            <p>When President Biden took office total gross debt was <b>${biden_start_debt_rounded} trillion</b>, meaning he has increased the national debt 
            by <b>${biden_debt_rounded} trillion</b>. This equates to:</p>
            <ul>
                <li><b>${biden_debt_per_person:,}</b> more debt per person in the U.S.</li>
                <li><b>${biden_debt_per_household:,}</b> more debt per household in the U.S.</li>
                <li><b>${biden_debt_per_child:,}</b> more debt per child in the U.S.</li>
            </ul>
            <p>The rate of debt accumulation during the Biden Administration has equaled:</p>
            <ul>
                <li><b>${biden_debt_per_day_rounded} billion</b> in new debt per day</li>
                <li><b>${biden_debt_per_hour} million</b> in new debt per hour</li>
                <li><b>${biden_debt_per_min} million</b> in new debt per minute</li>
                <li><b>${biden_debt_per_sec:,}</b> in new debt per second</li>
            </ul>
            <p>The debt one year ago was <b>${debt_year_ago_rounded} trillion</b>, meaning that the debt has increased by <b>${debt_increase_from_year_ago_rounded} trillion</b> over the past 12 months. The rate of increase since one year ago has equaled:</p>
            <ul>
                <li><b>${last_year_debt_per_day_rounded} billion</b> in new debt per day</li>
                <li><b>${last_year_debt_per_hour} million</b> in new debt per hour</li>
                <li><b>${last_year_debt_per_min} million</b> in new debt per minute</li>
                <li><b>${last_year_debt_per_sec:,}</b> in new debt per second</li>
            </ul>
        </div>
    </div>
    </html>
    '''

pdf = pdfkit.from_string(html, False, options={'enable-local-file-access': ''})
st.image(image_path)
cols = st.columns([1, 1, 1])
with cols[1]:
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"{CURRENT_DATE_STRING} Econ Summary Stats Report.pdf",
        mime="application/octet-stream"
    )

# Display in app
st.html(html.replace(style_html, ""))
#st.html(html.replace(f"""<img src={image_path} width = "70%" align = "middle">""", ""))