import streamlit as st
import debt_tracker

st.title('Debt Tracker')
st.write("In development.")

st.header('Current Debt')
st.write(f"The gross national debt is currently **${debt_tracker.current_debt_rounded:,} trillion**. This equates to:")
st.markdown(f""" - **\${debt_tracker.debt_per_person:,}** per person""") 
st.markdown(f"- **\${debt_tracker.debt_per_household:,}** per household")
st.markdown(f"- **\${debt_tracker.debt_per_child:,}** per child")

st.header('Biden Debt')
st.write(f"When President Biden took office total gross debt was **\${debt_tracker.biden_start_debt_rounded:,} trillion**, meaning he has increased the national debt by **${debt_tracker.biden_debt_rounded:,} trillion**. This equates to:")
st.markdown(f"- **${debt_tracker.biden_debt_per_person:,}** more debt per person")
st.markdown(f"- **${debt_tracker.biden_debt_per_household:,}** more debt per household")
st.markdown(f"- **${debt_tracker.biden_debt_per_child:,}** more debt per child")

st.header('Debt Accumulation Under Biden')
st.write("The rate of debt accumulation during the Biden Administration has equaled:")
st.markdown(f"- **${debt_tracker.biden_debt_per_day_rounded:,} billion** in new debt per day")
st.markdown(f"- **${debt_tracker.biden_debt_per_hour:,} million** in new debt per hour")
st.markdown(f"- **${debt_tracker.biden_debt_per_min:,} million** in new debt per minute")
st.markdown(f"- **${debt_tracker.biden_debt_per_sec:,}** in new debt per second")

st.header('Debt Accumulation in Past Year')
st.write(f"""The debt one year ago was **\${debt_tracker.debt_year_ago_rounded:,} trillion**, meaning that the debt has increased by **${debt_tracker.debt_increase_from_year_ago_rounded:,} trillion**
        over the past 12 months. This rate of increase equates to:""")
st.markdown(f"- **${debt_tracker.last_year_debt_per_day_rounded:,} billion** in new debt per day")
st.markdown(f"- **${debt_tracker.last_year_debt_per_hour:,} million** in new debt per hour")
st.markdown(f"- **${debt_tracker.last_year_debt_per_min:,} million** in new debt per minute")
st.markdown(f"- **${debt_tracker.last_year_debt_per_sec:,}** in new debt per second")