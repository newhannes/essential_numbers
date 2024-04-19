import streamlit as st
import streamlit.components.v1 as components
import pdfkit
from workhorses import cool_debt_metrics as cdm


# Add a button to download the HTML as a PDF
pdf = pdfkit.from_string(cdm.html, False)
st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"Debt Tracking Report {cdm.today}.pdf",
        mime="application/octet-stream"
    )

components.html(cdm.html, scrolling=False, height=4500, width=1000)

