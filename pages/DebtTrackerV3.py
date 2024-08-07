###### ------------------ STATIC MAIN FILE, PRODUCES HTML AND PDFS ------------------ ######
import streamlit as st
from workhorses.debt_tracker import debt_tracker_main
from workhorses.cool_debt_metrics_forV3 import main as cdm_main
import pdfkit
import shutil
from datetime import datetime

#### ---- FETCH DATA FROM THE WORKHORSES ---- ####
# if 'dt_today' not in st.session_state:
#     with st.spinner("Running Debt Tracker..."):
#         dt = debt_tracker_main()
#         #st.success("Debt Tracker has been updated!")
#         st.session_state.dt_today = dt['today']
# if ('cdm_today' not in st.session_state) or ('temp_dir' not in st.session_state):
#     with st.spinner("Running Cool Debt Metrics..."):
#         temp_dir, text_debt_to_assets, text_debt_to_wages, text_mortgage_rate, comparison_html, rate_increase_html, random_html, text_gdp_debt, html_credit_card, new_orders_html, household_html, cdm_today = cdm_main()
#         #st.success("Cool Debt Metrics has been updated!")
#         st.session_state.cdm_today = cdm_today
#         st.session_state.temp_dir = temp_dir


# for key in st.session_state:
#     st.write(key)
with st.spinner("Running Debt Tracker..."):
        dt = debt_tracker_main()
        st.session_state.dt_today = dt['today']
with st.spinner("Running Cool Debt Metrics..."):
        temp_dir, text_debt_to_assets, text_debt_to_wages, text_mortgage_rate, comparison_html, rate_increase_html, random_html, text_gdp_debt, html_credit_card, new_orders_html, household_html, cdm_today = cdm_main()
        st.session_state.temp_dir = temp_dir
        st.session_state.cdm_today = cdm_today
temp_dir = st.session_state.temp_dir
# if st.session_state.dt_today != datetime.today():
#     with st.spinner("Updating Debt Tracker..."):
#         debt_tracker_main.clear()
#         dt = debt_tracker_main()
#         st.session_state.dt_today = dt['today']
#if st.session_state.cdm_today != datetime.today():
#    with st.spinner("Updating Cool Debt Metrics..."):
        #cdm_main.clear()
#        temp_dir, text_debt_to_assets, text_debt_to_wages, text_mortgage_rate, comparison_html, rate_increase_html, random_html, text_gdp_debt, html_credit_card, new_orders_html, household_html, cdm_today = cdm_main()
#        st.session_state.cdm_today = cdm_today

#write the house budget header from inputs/HBR_Logo_Primary.png to the temp directory
# Define the source and destination paths
##source_path = 'inputs/HBR_Logo_Primary.png'
##destination_path = temp_dir + '/HBR_Logo_Primary.png'
image_path = "/mount/src/essential_numbers/inputs/HBR_Logo_Primary.png"
# Copy the file
##hutil.copy(source_path, destination_path)

def html_maker():
    basic_debt_html = f"""
    <div class="container">
            <div class="content">
                    <h2 style="text-align: center;">Current Debt</h2>
                    <p style="text-align: center;">The gross national debt is currently <strong>${dt['current_debt_rounded']:,} trillion</strong>. This equates to:</p>
                    <ul style="text-align: center;">
                            <strong>${dt['debt_per_person']:,}</strong> per person <br/>
                            <strong>${dt['debt_per_household']:,}</strong> per household <br/>
                            <strong>${dt['debt_per_child']:,}</strong> per child
                    </ul>
                    <img src={temp_dir+"/debt_timeline.png"} align = "middle">
                    <h2>Debt Accumulation under President Biden</h2>
                    <div>
                            <p>When President Biden took office total gross debt was <strong>${dt['biden_start_debt_rounded']:,} trillion</strong>, meaning he has increased the national debt by <strong>${dt['biden_debt_rounded']:,} trillion</strong>. This equates to:</p>
                            <ul>
                                    <li><strong>${dt['biden_debt_per_person']:,}</strong> more debt per person</li>
                                    <li><strong>${dt['biden_debt_per_household']:,}</strong> more debt per household</li>
                                    <li><strong>${dt['biden_debt_per_child']:,}</strong> more debt per child</li>
                            </ul>
                            
                            <p>The rate of debt accumulation during the Biden Administration has equaled:</p>
                            <ul>
                                    <li><strong>${dt['biden_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
                                    <li><strong>${dt['biden_debt_per_hour']:,} million</strong> in new debt per hour</li>
                                    <li><strong>${dt['biden_debt_per_min']:,} million</strong> in new debt per minute</li>
                                    <li><strong>${dt['biden_debt_per_sec']:,}</strong> in new debt per second</li>
                            </ul>
                    </div>
                    <div>
                    <p>{comparison_html}</p>
                    </div>
                    
                    <img src={temp_dir+"/budget_comparison.png"}>
                    

                    <h2>Debt Accumulation in Past Year</h2>
                    <div>
                    <p>The debt one year ago was <strong>${dt['debt_year_ago_rounded']:,} trillion</strong>, meaning that the debt has increased by <strong>${dt['debt_increase_from_year_ago_rounded']:,} trillion</strong> over the past 12 months. This rate of increase equates to:</p>
                    <ul>
                            <li><strong>${dt['last_year_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
                            <li><strong>${dt['last_year_debt_per_hour']:,} million</strong> in new debt per hour</li>
                            <li><strong>${dt['last_year_debt_per_min']:,} million</strong> in new debt per minute</li>
                            <li><strong>${dt['last_year_debt_per_sec']:,}</strong> in new debt per second</li>
                    </ul>
                    </div>
                    <div>
                    <p>{rate_increase_html}</p>
                    </div>
                    <img src={temp_dir+"/debt_increase.png"}>
            </div>
    </div>
    """

    #### ---- FINAL HTML ---- ####
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <center>
            <img src={image_path} width="500" align = "middle">
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
            <h1>Debt in Perspective</h1>
        </div>
        <div class="container">
            <div class="content">
                <h2>Debt to Wages</h2>
                <p>{text_debt_to_wages}</p>
                <img src={temp_dir+"/debt_to_wages.png"}>
                <br> </br>
                <h2>GDP Growth vs Debt Growth</h2>
                <p>{text_gdp_debt}</p>
                <img src={temp_dir+"/gdp_debt.png"}>
                <h2>Debt to Federal Assets</h2>
                <p>{text_debt_to_assets}</p>
                <img src={temp_dir+"/debt_to_assets.png"}>
            </div>
        </div>
        <div class="header">
            <h1>Why It Matters</h1>
        </div>
        <div class="container">
            <div class="content">
                <h2>Mortgage Rates</h2>
                <p>{text_mortgage_rate}</p>
                <img src={temp_dir+"/mortgage_rate.png"}>
                <h2>Credit Cards</h2>
                <p>{html_credit_card}</p>
                <img src={temp_dir+"/credit_card.png"}>
                <h2>Capital Investments</h2>
                <p>{new_orders_html}</p>
                <img src={temp_dir+"/new_orders.png"}>
            </div>
        </div>
        <div class="header">
            <h1>Looking Forward</h1>
        </div>
        <div class="container">
            <div class="content">
            <h2>CBO Projections</h2>
                <p>{random_html}</p>
                <img src={temp_dir+"/cbo_projections.png"}>
                <p>{household_html}</p>
                <img src={temp_dir+"/household_debt.png"}>
            </div>
            
        </div>

    </body>
    </html>
    """
    return html

if 'html' not in st.session_state:
    html = html_maker()
    st.session_state.html = html
html = st.session_state.html
# Convert the HTML string to a PDF
if 'pdf' not in st.session_state:
    pdf = pdfkit.from_string(html, False, options={"enable-local-file-access": ""})
    st.session_state.pdf = pdf
pdf = st.session_state.pdf
# Add a button to download the PDF
st.download_button(
    "⬇️ Download PDF",
    data=pdf,
    file_name=f"Debt Tracking Report {st.session_state.cdm_today}.pdf",
    mime="application/octet-stream"
)


st.image(image_path)
st.markdown("<h1 style='text-align: center;'>Debt Tracker V3</h1>", unsafe_allow_html=True)
