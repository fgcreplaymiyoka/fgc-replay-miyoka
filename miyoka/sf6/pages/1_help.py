import streamlit as st

with open("docs/how_to.md", "r") as f:
    st.markdown(f.read())
