import streamlit as st
from utils import hash_password
from database import users_collection

st.header("Register")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
bio = st.text_area("Bio")
if st.button("Register"):
    if users_collection.find_one({"username": username}):
        st.error("Username already exists")
    else:
        users_collection.insert_one({"username": username, "password": hash_password(password),"bio": ""})
        st.success("Registered successfully!")