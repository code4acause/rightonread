import streamlit as st
from utils import hash_password
from database import users_collection

st.header("Register")

# Add a radio button for user type selection
user_type = st.radio("Register as:", ("User", "Host"))

username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button("Register"):
    if users_collection.find_one({"username": username}):
        st.error("Username already exists")
    else:
        users_collection.insert_one({"username": username, "password": hash_password(password),"bio": "", "user_type" : user_type.lower(),
                                     "books_read": [],
                                     "total_questions" : 10,
                                     "correct_questions" : 8,
                                     "incorrect_questions" : 2})
        st.success("Registered successfully!")

st.page_link("pages/login.py", label="Please login here!")
