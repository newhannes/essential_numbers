import streamlit as st
from workhorses.debt_tracker import debt_tracker_main
from datetime import datetime
import tempfile, shutil
import pdfkit

def day_string_formatter(date):
        day = int(date.strftime('%d'))
        if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
        else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
        return date.strftime('%B ') + str(day) + suffix + date.strftime(', %Y')


dt = debt_tracker_main()
if dt['today'] != datetime.today():
        with st.spinner("Updating Debt Tracker..."):
                debt_tracker_main.clear()
                dt = debt_tracker_main()

today_string = day_string_formatter(dt['today'])

# Create a temporary directory
temp_dir = tempfile.mkdtemp()
source_path = 'inputs/HBR_Logo_Primary.png'
destination_path = temp_dir + '/HBR_Logo_Primary.png'
# Copy the file
shutil.copy(source_path, destination_path)


basic_debt_html = f"""
<h1 style='text-align: center;'>Debt Tracker</h1>
<h3 style='text-align: center;'> As of {today_string}</h3>
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
    </div>
</div>
"""
st.markdown(basic_debt_html, unsafe_allow_html=True)


to_replace = f"""<h1 style='text-align: center;'>Debt Tracker</h1>
<h3 style='text-align: center;'> As of {today_string}</h3>"""
html_for_pdf = f"""
<!DOCTYPE html>
<html>
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
            margin-top: 25px;
        }}
    </style>
    
    <img src={temp_dir + "/HBR_Logo_Primary.png"} align = "middle">
    
    <div class="header">
    <h1>Debt Tracker</h1>
    <h3 style='text-align: center;'> As of {today_string}</h3>
    </div>
        {basic_debt_html.replace(to_replace, "")}
</html>
"""
# Convert the HTML file to a PDF
pdf = pdfkit.from_string(html_for_pdf, False, options={"enable-local-file-access": ""})

# Add a button to download the PDF

st.download_button(
    "⬇️ Download PDF",
    data=pdf,
    file_name=f"Debt Tracking Report - {dt['today']}.pdf",
    mime="application/octet-stream"
)