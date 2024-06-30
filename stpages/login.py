import streamlit as st

username = st.text_input("Username")
if username:
    st.session_state.user = username
    st.success(f"Welcome, {username}!")
    st.rerun()