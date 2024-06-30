import streamlit as st
from database import competitions_collection, users_collection
from utils import check_user_logged_in
from bson import ObjectId

def app():
    check_user_logged_in()
    st.header("Mark Book as Read")
    
    user_id = st.session_state.user["_id"]
    
    # Get competitions the user has joined
    user_competitions = competitions_collection.find({"participants": user_id})
    competition_names = [comp['name'] for comp in user_competitions]
    
    if not competition_names:
        st.warning("You haven't joined any competitions yet.")
        return
    
    selected_competition_name = st.selectbox("Select Competition", competition_names)
    selected_competition = competitions_collection.find_one({"name": selected_competition_name})
    
    if selected_competition:
        book = st.selectbox("Select Book", selected_competition['books'])
        
        if st.button("Mark as Read"):
            users_collection.update_one(
                {"_id": user_id},
                {"$addToSet": {f"books_read.{str(selected_competition['_id'])}": book}}
            )
            st.success(f"You've marked '{book}' as read in the '{selected_competition_name}' competition!")
    else:
        st.error("Selected competition not found.")