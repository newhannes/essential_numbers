###### ------------------ STATIC MAIN FILE, PRODUCES HTML AND PDFS ------------------ ######
import streamlit as st
import workhorses.static_cool_debt_metrics as cdm
from workhorses.debt_tracker import debt_tracker_main
import pdfkit
import streamlit.components.v1 as components
import shutil
from datetime import datetime

dt = debt_tracker_main()
if dt['today'] != datetime.today().strftime('%Y-%m-%d'):
    with st.spinner("Updating Debt Tracker..."):
        debt_tracker_main.clear()
        dt = debt_tracker_main()

#write the house budget header from inputs/HBR_Logo_Primary.png to the temp directory
# Define the source and destination paths
source_path = 'inputs/HBR_Logo_Primary.png'
destination_path = cdm.temp_dir + '/HBR_Logo_Primary.png'

# Copy the file
shutil.copy(source_path, destination_path)

basic_debt_html = f"""
<div class="container">
    <div class="content">
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
            <li><strong>${dt['biden_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['biden_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['biden_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['biden_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
        <h2>Debt Accumulation in Past Year</h2>
        <p>The debt one year ago was <strong>${dt['debt_year_ago_rounded']:,} trillion</strong>, meaning that the debt has increased by <strong>${dt['debt_increase_from_year_ago_rounded']:,} trillion</strong> over the past 12 months. This rate of increase equates to:</p>
        <ul>
            <li><strong>${dt['last_year_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['last_year_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['last_year_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['last_year_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
    </div>
</div>
"""

#### ---- FINAL HTML ---- ####
html = f"""
<!DOCTYPE html>
<html>
<head>
    <center>
        <img src={cdm.temp_dir + "/HBR_Logo_Primary.png"} width="500" align = "middle">
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
            <p>{cdm.text_debt_to_wages}</p>
            <img src={cdm.temp_dir+"/debt_to_wages.png"}>
            <br> </br>
            <h2>Mortgage Rates</h2>
            <p>{cdm.text_mortgage_rate}</p>
            <img src={cdm.temp_dir+"/mortgage_rate.png"}>
            <h2>Rate of Increase</h2>
            <p>{cdm.rate_increase_html}</p>
            <img src={cdm.temp_dir+"/debt_increase.png"}>
            <h2>GDP Growth vs Debt Growth</h2>
            <p>{cdm.text_gdp_debt}</p>
            <img src={cdm.temp_dir+"/gdp_debt.png"}>
            <h2>Debt to Federal Assets</h2>
            <p>{cdm.text_debt_to_assets}</p>
            <img src={cdm.temp_dir+"/debt_to_assets.png"}>
        </div>
    </div>
    <div class="header">
        <h1>Looking Forward</h1>
    </div>
    <div class="container">
        <div class="content">
        <h2>CBO Projections</h2>
            <p>{cdm.random_html}</p>
            <img src={cdm.temp_dir+"/cbo_projections.png"}>
        <h2>Our Budget vs President's Budget</h2>
            <p>{cdm.comparison_html}</p>
            <img src={cdm.temp_dir+"/budget_comparison.png"}>
        </div>
    </div>

</body>
</html>
"""

# Convert the HTML file to a PDF
pdf = pdfkit.from_string(html, False, options={"enable-local-file-access": ""})

# Add a button to download the PDF
st.download_button(
    "⬇️ Download PDF",
    data=pdf,
    file_name=f"Debt Tracking Report {cdm.today}.pdf",
    mime="application/octet-stream"
)

def section_write(section_title, section_text, section_image):
    st.markdown(f"<h2>{section_title}</h2>", unsafe_allow_html=True)
    st.markdown(section_text, unsafe_allow_html=True)
    st.image(section_image)


# Write out the text and images using streamlit
st.image(cdm.temp_dir + "/HBR_Logo_Primary.png")
st.markdown("<h1 style='text-align: center;'>Debt Tracker</h1>", unsafe_allow_html=True)
st.markdown(basic_debt_html, unsafe_allow_html=True)
#understanding the debt
st.markdown("<h1 style='text-align: center;'>Debt in Perspective</h1>", unsafe_allow_html=True)
#debt to wages
section_write("Debt to Wages", cdm.text_debt_to_wages, cdm.temp_dir + "/debt_to_wages.png")
#mortgage rates
section_write("Mortgage Rates", cdm.text_mortgage_rate, cdm.temp_dir + "/mortgage_rate.png")
#rate of increase
section_write("Rate of Increase", cdm.rate_increase_html, cdm.temp_dir + "/debt_increase.png")
#gdp vs debt
section_write("GDP Growth vs Debt Growth", cdm.text_gdp_debt, cdm.temp_dir + "/gdp_debt.png")
#debt to federal assets
section_write("Debt to Federal Assets", cdm.text_debt_to_assets, cdm.temp_dir + "/debt_to_assets.png")
st.markdown("<h1 style='text-align: center;'>Looking Forward</h1>", unsafe_allow_html=True)
#cbo projections
section_write("CBO Projections", cdm.random_html, cdm.temp_dir + "/cbo_projections.png")
#budget comparison
section_write("House Budget Committee vs President's Budget", cdm.comparison_html, cdm.temp_dir + "/budget_comparison.png")

