import streamlit as st
import hashlib

def check_user_logged_in():
    if not st.session_state.user:
        st.warning("Please log in to access this page")
        st.stop()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()
