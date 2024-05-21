import streamlit as st
from workhorses.debt_tracker import debt_tracker_main
from datetime import datetime


def day_string_formatter(date):
        day = int(date.strftime('%d'))
        if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
        else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
        return date.strftime('%B ') + str(day) + suffix + date.strftime(', %Y')


dt = debt_tracker_main()
if dt['today'] != datetime.today():
        with st.spinner("Updating Debt Tracker..."):
                debt_tracker_main.clear()
                dt = debt_tracker_main()

today_string = day_string_formatter(dt['today'])
st.markdown("<h1 style='text-align: center; color: black;'>Debt Tracker</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: black;'> As of {today_string}</h3>", unsafe_allow_html=True)

# Current Debt
st.markdown("<h2>Current Debt</h2>", unsafe_allow_html=True)
st.write(f"The gross national debt is currently **${dt['current_debt_rounded']:,} trillion**. This equates to:")
st.markdown(f""" - **\${dt['debt_per_person']:,}** per person""") 
st.markdown(f"- **\${dt['debt_per_household']:,}** per household")
st.markdown(f"- **\${dt['debt_per_child']:,}** per child")
# Biden Debt
st.markdown("<h2>Biden Debt</h2>", unsafe_allow_html=True)
st.write(f"When President Biden took office total gross debt was **\${dt['biden_start_debt_rounded']:,} trillion**, meaning he has increased the national debt by **${dt['biden_debt_rounded']:,} trillion**. This equates to:")
st.markdown(f"- **${dt['biden_debt_per_person']:,}** more debt per person")
st.markdown(f"- **${dt['biden_debt_per_household']:,}** more debt per household")
st.markdown(f"- **${dt['biden_debt_per_child']:,}** more debt per child")
# Biden Debt Accumulation
st.write("The rate of debt accumulation during the Biden Administration has equaled:")
st.markdown(f"- **${dt['biden_debt_per_month']:,} billion** in new debt per month")
st.markdown(f"- **${dt['biden_debt_per_day_rounded']:,} billion** in new debt per day")
st.markdown(f"- **${dt['biden_debt_per_hour']:,} million** in new debt per hour")
st.markdown(f"- **${dt['biden_debt_per_min']:,} million** in new debt per minute")
st.markdown(f"- **${dt['biden_debt_per_sec']:,}** in new debt per second")
# Debt Accumulation in Past Year
st.markdown("<h2>Debt Accumulation in Past Year</h2>", unsafe_allow_html=True)
st.write(f"""The debt one year ago was **\${dt['debt_year_ago_rounded']:,} trillion**, meaning that the debt has increased by **${dt['debt_increase_from_year_ago_rounded']:,} trillion**
        over the past 12 months. This rate of increase equates to:""")
st.markdown(f"- **${dt['last_year_debt_per_month']:,} billion** in new debt per month")
st.markdown(f"- **${dt['last_year_debt_per_day_rounded']:,} billion** in new debt per day")
st.markdown(f"- **${dt['last_year_debt_per_hour']:,} million** in new debt per hour")
st.markdown(f"- **${dt['last_year_debt_per_min']:,} million** in new debt per minute")
st.markdown(f"- **${dt['last_year_debt_per_sec']:,}** in new debt per second")

        
        