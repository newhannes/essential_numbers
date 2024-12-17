import pdfkit
import pandas as pd
from workhorses.gdp_report.main import main as gdp_report_main
import streamlit as st

with st.spinner("Generating GDP Report..."):
    html_string = gdp_report_main()

image_path = 'inputs/HBR_Logo_Primary.png'
st.image(image_path)
# display html
# st.html(html_string)
# st.image("output/charts/contributors.png")


# offer PDF download 
pdf = pdfkit.from_string(html_string, False, options={"enable-local-file-access": ""})

# Show the pdf 
st.html(f'<embed src="data:application/pdf;base64,{pdf}" width="100%" height="800"></embed>')


cols = st.columns([1, 1, 1])
with cols[1]:
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"GDP Report.pdf",
        mime="application/octet-stream"
    )







