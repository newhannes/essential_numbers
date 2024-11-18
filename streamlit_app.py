import streamlit as st

pg = st.navigation(
    [
    st.Page("app_pages/Home.py"),
    st.Page("app_pages/Debt_Tracker.py"),
    st.Page("app_pages/Inflation.py"),
    st.Page("app_pages/Labor_Data.py"),
    st.Page("app_pages/JCA_Quick_Stats.py"),
    st.Page("app_pages/Summary_Stats.py")
    ]
    )

pg.run()