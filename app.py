import streamlit as st

st.title("🌍 BCRA Project")

name = st.text_input("Enter your name")

if name:
    st.success(f"Welcome, {name} 🚀")