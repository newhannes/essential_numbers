import streamlit as st

rd_file_path = "README.md"
with open(rd_file_path, "r") as f:
        readme_text = f.read()
        st.markdown(readme_text)