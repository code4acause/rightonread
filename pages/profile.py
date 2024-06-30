import streamlit as st
from database import users_collection
from database import user_stats_collection
from database import competitions_collection

from utils import check_user_logged_in

def update_profile(user_id, new_bio):
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"bio": new_bio}}
    )
    st.success("Profile updated successfully!")
    st.session_state.bio = new_bio  # Update session state
# user_stats_collection.find_one({"user_id": user_id})
check_user_logged_in()
user = users_collection.find_one({"_id": st.session_state.user["_id"]})
print(user)
st.header(f"Profile {user['username']}")
st.write(f"Here are your statistics, {user['username']}")
st.write("You have answered: " + str(user.get("correct_answers")) +" out of " + str(user.get("total_questions")) + " questions correctly")

comps = list(competitions_collection.find({"participants": user["_id"]}))
st.write("You are part of " + str(len(comps)) + " competitions")
try:
    numbooks = list(user.get("books_read")) 
    st.write("You have read " + str(len(numbooks)) + " books")
except:
    st.write("You have not read any books yet")

st.write("Your phone number is " + str(user.get("phone_number")))


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