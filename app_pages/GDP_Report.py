import pdfkit
import pandas as pd
from workhorses.gdp_report.main import main
import streamlit as st

with st.spinner("Generating GDP Report..."):
    main()

image_path = 'inputs/HBR_Logo_Primary.png'
st.image(image_path)
# display html
html = open("output/GDP_REPORT.html", "r").read()
st.write(html)

# offer PDF download 
pdf = pdfkit.from_file("output/GDP_REPORT.html", "output/GDP_REPORT.pdf")
cols = st.columns([1, 1, 1])
with cols[1]:
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"GDP Report.pdf",
        mime="application/octet-stream"
    )







