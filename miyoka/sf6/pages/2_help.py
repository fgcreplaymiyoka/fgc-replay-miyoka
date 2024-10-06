import streamlit as st

with open("docs/hot_to.md", "r") as f:
    st.markdown(f.read())
