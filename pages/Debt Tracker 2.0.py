import streamlit as st
import streamlit.components.v1 as components
import os
#import sys
#sys.path.insert(0, r"C:\Users\DSikkink\OneDrive - US House of Representatives\Python\Essential Numbers\workhorses")
from workhorses import cool_debt_metrics as cdm

components.html(cdm.html, scrolling=False, height=4500, width=1000)
