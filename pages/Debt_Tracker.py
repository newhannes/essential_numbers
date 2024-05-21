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
# st.markdown("<h1 style='text-align: center; color: black;'>Debt Tracker</h1>", unsafe_allow_html=True)
# st.markdown(f"<h3 style='text-align: center; color: black;'> As of {today_string}</h3>", unsafe_allow_html=True)

# # Current Debt
# st.markdown("<h2>Current Debt</h2>", unsafe_allow_html=True)
# st.write(f"The gross national debt is currently **${dt['current_debt_rounded']:,} trillion**. This equates to:")
# st.markdown(f""" - **\${dt['debt_per_person']:,}** per person""") 
# st.markdown(f"- **\${dt['debt_per_household']:,}** per household")
# st.markdown(f"- **\${dt['debt_per_child']:,}** per child")
# # Biden Debt
# st.markdown("<h2>Biden Debt</h2>", unsafe_allow_html=True)
# st.write(f"When President Biden took office total gross debt was **\${dt['biden_start_debt_rounded']:,} trillion**, meaning he has increased the national debt by **${dt['biden_debt_rounded']:,} trillion**. This equates to:")
# st.markdown(f"- **${dt['biden_debt_per_person']:,}** more debt per person")
# st.markdown(f"- **${dt['biden_debt_per_household']:,}** more debt per household")
# st.markdown(f"- **${dt['biden_debt_per_child']:,}** more debt per child")
# # Biden Debt Accumulation
# st.write("The rate of debt accumulation during the Biden Administration has equaled:")
# st.markdown(f"- **${dt['biden_debt_per_month']:,} billion** in new debt per month")
# st.markdown(f"- **${dt['biden_debt_per_day_rounded']:,} billion** in new debt per day")
# st.markdown(f"- **${dt['biden_debt_per_hour']:,} million** in new debt per hour")
# st.markdown(f"- **${dt['biden_debt_per_min']:,} million** in new debt per minute")
# st.markdown(f"- **${dt['biden_debt_per_sec']:,}** in new debt per second")
# # Debt Accumulation in Past Year
# st.markdown("<h2>Debt Accumulation in Past Year</h2>", unsafe_allow_html=True)
# st.write(f"""The debt one year ago was **\${dt['debt_year_ago_rounded']:,} trillion**, meaning that the debt has increased by **${dt['debt_increase_from_year_ago_rounded']:,} trillion**
#         over the past 12 months. This rate of increase equates to:""")
# st.markdown(f"- **${dt['last_year_debt_per_month']:,} billion** in new debt per month")
# st.markdown(f"- **${dt['last_year_debt_per_day_rounded']:,} billion** in new debt per day")
# st.markdown(f"- **${dt['last_year_debt_per_hour']:,} million** in new debt per hour")
# st.markdown(f"- **${dt['last_year_debt_per_min']:,} million** in new debt per minute")
# st.markdown(f"- **${dt['last_year_debt_per_sec']:,}** in new debt per second")

        
basic_debt_html = f"""
<img src={'../inputs/HBR_Logo_Primary.png'} width="500" align = "middle">
<h1 style='text-align: center; color: black;'>Debt Tracker</h1>
<h3 style='text-align: center; color: black;'> As of {today_string}</h3>
<div class="container">
    <div class="content">
        <h2>Current Debt</h2>
        <p>The gross national debt is currently <strong>${dt['current_debt_rounded']:,} trillion</strong>. This equates to:</p>
        <ul>
            <li><strong>${dt['debt_per_person']:,}</strong> per person</li>
            <li><strong>${dt['debt_per_household']:,}</strong> per household</li>
            <li><strong>${dt['debt_per_child']:,}</strong> per child</li>
        </ul>
        <h2>Debt Accumulation under President Biden</h2>
        <p>When President Biden took office total gross debt was <strong>${dt['biden_start_debt_rounded']:,} trillion</strong>, meaning he has increased the national debt by <strong>${dt['biden_debt_rounded']:,} trillion</strong>. This equates to:</p>
        <ul>
            <li><strong>${dt['biden_debt_per_person']:,}</strong> more debt per person</li>
            <li><strong>${dt['biden_debt_per_household']:,}</strong> more debt per household</li>
            <li><strong>${dt['biden_debt_per_child']:,}</strong> more debt per child</li>
        </ul>
        <p>The rate of debt accumulation during the Biden Administration has equaled:</p>
        <ul>
            <li><strong>${dt['biden_debt_per_month']:,} billion</strong> in new debt per month</li>
            <li><strong>${dt['biden_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['biden_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['biden_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['biden_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
        <h2>Debt Accumulation in Past Year</h2>
        <p>The debt one year ago was <strong>${dt['debt_year_ago_rounded']:,} trillion</strong>, meaning that the debt has increased by <strong>${dt['debt_increase_from_year_ago_rounded']:,} trillion</strong> over the past 12 months. This rate of increase equates to:</p>
        <ul>
            <li><strong>${dt['last_year_debt_per_month']:,} billion</strong> in new debt per month</li>
            <li><strong>${dt['last_year_debt_per_day_rounded']:,} billion</strong> in new debt per day</li>
            <li><strong>${dt['last_year_debt_per_hour']:,} million</strong> in new debt per hour</li>
            <li><strong>${dt['last_year_debt_per_min']:,} million</strong> in new debt per minute</li>
            <li><strong>${dt['last_year_debt_per_sec']:,}</strong> in new debt per second</li>
        </ul>
    </div>
</div>
"""
st.markdown(basic_debt_html, unsafe_allow_html=True)