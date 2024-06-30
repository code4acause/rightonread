import streamlit as st
from database import users_collection, confirmConnection
from utils import hash_password

st.header("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button("Login"):
    user = users_collection.find_one({"username": username, "password": hash_password(password)})
    if user:
        st.session_state.user = user
        st.success("Logged in successfully!")
        st.rerun()
    else:
        st.error("Invalid credentials")

if st.button("Ping"):
    st.write(confirmConnection())