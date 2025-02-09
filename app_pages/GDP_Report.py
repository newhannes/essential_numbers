import pdfkit
import pandas as pd
from workhorses.gdp_report.main import main as gdp_report_main
import streamlit as st
import base64

with st.spinner("Generating GDP Report..."):
    html_string = gdp_report_main()

image_path = 'inputs/HBR_Logo_Primary.png'
st.image(image_path)


# offer PDF download 
pdf = pdfkit.from_string(html_string, False, options={"enable-local-file-access": ""})

cols = st.columns([1, 1, 1])
with cols[1]:
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"GDP Report.pdf",
        mime="application/octet-stream"
    )







