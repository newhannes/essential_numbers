import streamlit as st
from workhorses.debt_tracker import debt_tracker_main
from workhorses import debt_visuals, debt_visual2, debt_visual3


dt = debt_tracker_main()

st.markdown("<h1 style='text-align: center; color: black;'>Debt Tracker</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: black;'> As of {dt['today']}</h3>", unsafe_allow_html=True)
#st.write("In development.



with st.columns(1)[0]:
        st.markdown("<h2 style='text-align: center; color: black;'>Current Debt</h2>", unsafe_allow_html=True)
        cols1 = st.columns(2)
        with cols1[0]:
                st.write(f"The gross national debt is currently **${dt['current_debt_rounded']:,} trillion**. This equates to:")
                st.markdown(f""" - **\${dt['debt_per_person']:,}** per person""") 
                st.markdown(f"- **\${dt['debt_per_household']:,}** per household")
                st.markdown(f"- **\${dt['debt_per_child']:,}** per child")
                
        #with cols1[1]:
                #st.write("Debt is better understood in context of the economy. Comparing the historic debt to GDP ratio to our current and projected ratios shows the unprecedented nature of our current situation.")
                #st.plotly_chart(debt_visuals.fig)

row2 = st.columns(1)
with row2[0]:
        st.markdown("<h2 style='text-align: center; color: black;'>Biden Debt</h2>", unsafe_allow_html=True)
        cols2 = st.columns(2)
        with cols2[0]:       
                #st.header('Biden Debt')
                st.write(f"When President Biden took office total gross debt was **\${dt['biden_start_debt_rounded']:,} trillion**, meaning he has increased the national debt by **${dt['biden_debt_rounded']:,} trillion**. This equates to:")
                st.markdown(f"- **${dt['biden_debt_per_person']:,}** more debt per person")
                st.markdown(f"- **${dt['biden_debt_per_household']:,}** more debt per household")
                st.markdown(f"- **${dt['biden_debt_per_child']:,}** more debt per child")
                
                st.write("The rate of debt accumulation during the Biden Administration has equaled:")
                st.markdown(f"- **${dt['biden_debt_per_day_rounded']:,} billion** in new debt per day")
                st.markdown(f"- **${dt['biden_debt_per_hour']:,} million** in new debt per hour")
                st.markdown(f"- **${dt['biden_debt_per_min']:,} million** in new debt per minute")
                st.markdown(f"- **${dt['biden_debt_per_sec']:,}** in new debt per second")
        #with cols2[1]:
                #st.write("President Biden's FY25 budget doubled down on his disregard for the national debt. The HBCR budget offers a return to the fiscal sanity.")
         #       st.plotly_chart(debt_visual2.fig)

row3 = st.columns(1)
with row3[0]:
        st.markdown("<h2 style='text-align: center; color: black;'>Debt Accumulation in Past Year</h2>", unsafe_allow_html=True)
        cols3 = st.columns(2)
        with cols3[0]:
                #st.header('Debt Accumulation in Past Year')
                st.write(f"""The debt one year ago was **\${dt['debt_year_ago_rounded']:,} trillion**, meaning that the debt has increased by **${dt['debt_increase_from_year_ago_rounded']:,} trillion**
                        over the past 12 months. This rate of increase equates to:""")
                st.markdown(f"- **${dt['last_year_debt_per_day_rounded']:,} billion** in new debt per day")
                st.markdown(f"- **${dt['last_year_debt_per_hour']:,} million** in new debt per hour")
                st.markdown(f"- **${dt['last_year_debt_per_min']:,} million** in new debt per minute")
                st.markdown(f"- **${dt['last_year_debt_per_sec']:,}** in new debt per second")
        #with cols3[1]:
                #st.write("The rate of increase in recent years is mad crazy dawg.")
                #st.plotly_chart(debt_visual3.fig)

        
        