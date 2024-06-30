import streamlit as st
from database import users_collection, confirmConnection
from utils import hash_password

st.header("Login")
col1, col2 = st.columns(2)
username = col1.text_input("Username")
password = col2.text_input("Password", type="password")
if password:
    user = users_collection.find_one({"username": username, "password": hash_password(password)})
    if user:
        st.session_state.user = user
        st.success("Logged in successfully!")
        st.rerun()
    else:
        st.error("Invalid credentials")

st.page_link("pages/register.py", label="Or, register here!")