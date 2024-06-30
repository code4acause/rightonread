import streamlit as st
from database import competitions_collection
from utils import check_user_logged_in
from bson import ObjectId
from streamlit.runtime.scriptrunner import RerunData, RerunException
import datetime

check_user_logged_in()
user = st.session_state.user

if user["user_type"] == "host":
    st.header("Manage Competitions")
    my_competitions = competitions_collection.find({"creator": st.session_state.user["_id"]})
    for comp in my_competitions:
        col1, col2 = st.columns(2)
        with col1:
            st.write(comp['name'])
        with col2:
            if st.button(f"View {comp['name']}", key=f"view_{comp['_id']}"):
                st.query_params["id"] = str(comp['_id'])
                st.switch_page("./pages/competition_detail.py")
    st.stop()

st.header(f"Competitions for {user['username']}")

# List joined competitions
st.subheader("Joined Competitions")
joined_competitions = competitions_collection.find({"participants": st.session_state.user["_id"]})
for comp in joined_competitions:
    col1, col2, col3, col4 = st.columns(4)
    col1.write(f"**{comp['name']}**")
    col2.write(comp['description'])
    with col3:
        if st.button(f"Compete", key=f"compete_{comp['_id']}"):
            st.query_params["id"] = str(comp['_id'])
            st.switch_page("./pages/compete.py")
    with col4:
        if st.button(f"View", key=f"view_{comp['_id']}"):
            st.query_params["id"] = str(comp['_id'])
            st.switch_page("./pages/competition_detail.py")

# List other competitions
st.subheader("Open Competitions")
other_competitions = competitions_collection.find({"participants": {"$ne": st.session_state.user["_id"]}})
for comp in other_competitions:
    col1, col2, col3, col4 = st.columns(4)
    col1.write(f"**{comp['name']}**")
    col2.write(comp['description'])
    with col3:
        if st.button(f"Join", key=f"join_{comp['_id']}"):
            competitions_collection.update_one(
                {"_id": comp["_id"]},
                {"$addToSet": {"participants": st.session_state.user["_id"]}}
            )
            st.success(f"Joined {comp['name']} successfully!")
            st.rerun()
    with col4:
        if st.button(f"View", key=f"view_{comp['_id']}"):
            st.query_params["id"] = str(comp['_id'])
            st.switch_page("./pages/competition_detail.py")

# Rest of the code for creating a competition remains the same
# ...