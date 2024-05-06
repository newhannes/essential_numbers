import streamlit as st
#os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")
from st_pages import Page, add_page_title, show_pages

show_pages(
    [
        Page("pages/Home.py", "Home"),
        Page("pages/Debt_Tracker.py", "Debt Tracker"),
        #Page("pages/Debt_Tracker_2.0.py", "Debt Tracker 2.0 TEST"),
        Page("pages/Static_Debt_Tracker.py", "Static Debt Tracker"),
        Page("pages/DebtTrackerV3.py", "Debt Tracker V3"),
        Page("pages/Labor_Data.py", "Employment and Wages"),
        Page("pages/About.py", "About")
    ]
)
# page = st.sidebar.radio("Go to page", ["Home", "Debt Tracker", "Inflation", "Job Market and Wages", "Interest Rates", "Consumer Debt", "Oil and Gas", "About"])
# rd_file_path = "README.md"

# st.title("Essential Numbers")


    
# if page == "About":
#      with open(rd_file_path, "r") as f:
#         readme_text = f.read()
#         st.markdown(readme_text)
