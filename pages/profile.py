import streamlit as st
from database import users_collection
from utils import check_user_logged_in

check_user_logged_in()
st.header("Profile")
user = users_collection.find_one({"_id": st.session_state.user["_id"]})
st.write(f"Username: {user['username']}")
st.write(f"Bio: {user['bio']}")

if st.button("Edit Profile"):
    new_bio = st.text_area("New Bio", value=user['bio'])
    if st.button("Save Changes"):
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"bio": new_bio}}
        )
        st.success("Profile updated successfully!")