import streamlit as st
from database import users_collection
from utils import check_user_logged_in

def update_profile(user_id, new_bio):
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"bio": new_bio}}
    )
    st.success("Profile updated successfully!")
    st.session_state.bio = new_bio  # Update session state

check_user_logged_in()

st.write(st.query_params.get("view_id")) # This will print the view_id query parameter

user = users_collection.find_one({"_id": st.session_state.user["_id"]})
st.header(f"Profile {user['username']}")

# Initialize session state for editing mode and bio
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'bio' not in st.session_state:
    st.session_state.bio = user['bio']

if st.session_state.editing:
    new_bio = st.text_area("Bio", value=st.session_state.bio)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes"):
            update_profile(user["_id"], new_bio)
            st.session_state.editing = False
    with col2:
        if st.button("Cancel"):
            st.session_state.editing = False
            st.session_state.bio = user['bio']
else:
    st.write(f"Bio: {st.session_state.bio}")
    if st.button("Edit Profile"):
        st.session_state.editing = True

# Display other user information or statistics here