import streamlit as st
import pandas as pd
#import os
from debt_tracker import debt_tracker
#os.chdir(r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers")

page = st.sidebar.radio("Go to page", ["Home", "Debt Tracker", "Inflation", "Job Market and Wages", "Interest Rates", "Consumer Debt", "Oil and Gas", "About"])
rd_file_path = "README.md"

if page == "Home":
    st.title("Essential Numbers")
    st.write("A dashboard to store essential numbers used by the House Budget Committee. Work in progress.")

if page == "Debt Tracker":
    debt_tracker()

    st.title('Debt Tracker')
    st.write("In development.")

    st.header('Current Debt')
    st.write(f"The gross national debt is currently **${current_debt_rounded:,} trillion**. This equates to:")
    st.markdown(f"**${debt_per_person:,}** per person")
    st.write(f"**${debt_per_household:,}** per household")
    st.write(f"**${debt_per_child:,}** per child")

    st.header('Biden Debt')
    st.write(f"When President Biden took office total gross debt was **\${biden_start_debt_rounded:,} trillion**, meaning he has increased the national debt by **${biden_debt_rounded:,} trillion**. This equates to:")
    st.write(f"**${biden_debt_per_person:,}** more debt per person")
    st.write(f"**${biden_debt_per_household:,}** more debt per household")
    st.write(f"**${biden_debt_per_child:,}** more debt per child")

    st.header('Debt Accumulation Under Biden')
    st.write("The rate of debt accumulation during the Biden Administration has equaled:")
    st.write(f"**${biden_debt_per_day_rounded:,} billion** in new debt per day")
    st.write(f"**${biden_debt_per_hour:,} million** in new debt per hour")
    st.write(f"**${biden_debt_per_min:,} million** in new debt per minute")
    st.write(f"**${biden_debt_per_sec:,}** in new debt per second")

    st.header('Debt Accumulation in Past Year')
    st.write(f"""The debt one year ago was **\${debt_year_ago_rounded:,} trillion**, meaning that the debt has increased by **${debt_increase_from_year_ago_rounded:,} trillion**
            over the past 12 months. This rate of increase equates to:""")
    st.write(f"**${last_year_debt_per_day_rounded:,} billion** in new debt per day")
    st.write(f"**${last_year_debt_per_hour:,} million** in new debt per hour")
    st.write(f"**${last_year_debt_per_min:,} million** in new debt per minute")
    st.write(f"**${last_year_debt_per_sec:,}** in new debt per second")
    
    # st.title('Debt Tracker')
    # st.write("In development.")

    # st.header('Current Debt')
    # st.write(f"The gross national debt is currently **${debt_tracker.current_debt_rounded:,} trillion**. This equates to:")
    # st.markdown(f"**${debt_tracker.debt_per_person:,}** per person")
    # st.write(f"**${debt_tracker.debt_per_household:,}** per household")
    # st.write(f"**${debt_tracker.debt_per_child:,}** per child")

    # st.header('Biden Debt')
    # st.write(f"When President Biden took office total gross debt was **\${debt_tracker.biden_start_debt_rounded:,} trillion**, meaning he has increased the national debt by **${debt_tracker.biden_debt_rounded:,} trillion**. This equates to:")
    # st.write(f"**${debt_tracker.biden_debt_per_person:,}** more debt per person")
    # st.write(f"**${debt_tracker.biden_debt_per_household:,}** more debt per household")
    # st.write(f"**${debt_tracker.biden_debt_per_child:,}** more debt per child")

    # st.header('Debt Accumulation Under Biden')
    # st.write("The rate of debt accumulation during the Biden Administration has equaled:")
    # st.write(f"**${debt_tracker.biden_debt_per_day_rounded:,} billion** in new debt per day")
    # st.write(f"**${debt_tracker.biden_debt_per_hour:,} million** in new debt per hour")
    # st.write(f"**${debt_tracker.biden_debt_per_min:,} million** in new debt per minute")
    # st.write(f"**${debt_tracker.biden_debt_per_sec:,}** in new debt per second")

    # st.header('Debt Accumulation in Past Year')
    # st.write(f"""The debt one year ago was **\${debt_tracker.debt_year_ago_rounded:,} trillion**, meaning that the debt has increased by **${debt_tracker.debt_increase_from_year_ago_rounded:,} trillion**
    #         over the past 12 months. This rate of increase equates to:""")
    # st.write(f"**${debt_tracker.last_year_debt_per_day_rounded:,} billion** in new debt per day")
    # st.write(f"**${debt_tracker.last_year_debt_per_hour:,} million** in new debt per hour")
    # st.write(f"**${debt_tracker.last_year_debt_per_min:,} million** in new debt per minute")
    # st.write(f"**${debt_tracker.last_year_debt_per_sec:,}** in new debt per second")

    
if page == "About":
     with open(rd_file_path, "r") as f:
        readme_text = f.read()
        st.markdown(readme_text)
