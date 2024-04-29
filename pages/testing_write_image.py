import streamlit as st
import plotly.express as px

from workhorses.cool_debt_metrics import fig1
st.title("Testing Writing Image")

fig1.write_image("fig1.png")

st.write("Download")
st.image("fig1.png")