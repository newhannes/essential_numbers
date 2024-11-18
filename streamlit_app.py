import streamlit as st
# from st_pages import Page, add_page_title, show_pages

# show_pages(
#     [
#         Page("pages/Home.py", "Home"),
#         Page("pages/Debt_Tracker.py", "Debt Tracker"),
#         Page("pages/Static_Debt_Tracker.py", "Static Debt Tracker"),
#         Page("pages/DebtTrackerV3.py", "Debt Tracker V3"),
#         Page("pages/JCA_Quick_Stats.py", "JCA Favorites"),
#         Page("pages/Labor_Data.py", "Employment and Wages"),
#         Page("pages/Inflation.py", "Inflation"),
#         Page("pages/About.py", "About")
#     ]
# )




pg = st.navigation(
    [
    st.Page("app_pages/Home.py"),
    st.Page("app_pages/Debt_Tracker.py"),
    st.Page("app_pages/Inflation.py"),
    st.Page("app_pages/Labor_Data.py"),
    st.Page("app_pages/JCA_Quick_Stats.py")
    ]
    )


pg.run()