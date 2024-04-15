import streamlit as st
import pandas as pd
#import os
import debt_tracker
#os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")
from st_pages import Page, add_page_title, show_pages

show_pages(
    [
        Page("pages/Home.py", "Home"),
        Page("pages/Debt Tracker.py", "Debt Tracker"),
        Page("pages/About.py", "About")
    ]
)
# page = st.sidebar.radio("Go to page", ["Home", "Debt Tracker", "Inflation", "Job Market and Wages", "Interest Rates", "Consumer Debt", "Oil and Gas", "About"])
# rd_file_path = "README.md"

# st.title("Essential Numbers")
# st.write("A dashboard to store essential numbers used by the House Budget Committee. Work in progress.")




    
# if page == "About":
#      with open(rd_file_path, "r") as f:
#         readme_text = f.read()
#         st.markdown(readme_text)
