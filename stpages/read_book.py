import streamlit as st
from database import db

st.write(db["books"].find({}))