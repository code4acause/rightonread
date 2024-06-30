import streamlit as st
from database import competitions_collection, users_collection
from utils import check_user_logged_in
from bson import ObjectId

check_user_logged_in()
competition_id = st.query_params.get("id")
if not competition_id:
    st.error("No competition ID provided")
    st.stop()

competition = competitions_collection.find_one({"_id": ObjectId(competition_id)})
if competition:
    st.header(competition['name'])
    st.write(competition['description'])
    st.write(f"Start Date: {competition['start_date']}")
    st.write(f"End Date: {competition['end_date']}")
    
    # Display leaderboard
    st.subheader("Leaderboard")
    leaderboard = []
    for participant_id in competition['participants']:
        user = users_collection.find_one({"_id": participant_id})
        books_read = len(user.get('books_read', {}).get(str(competition['_id']), []))
        leaderboard.append((user['username'], books_read))
    
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    for rank, (username, books_read) in enumerate(leaderboard, 1):
        st.write(f"{rank}. {username}: {books_read} books read")
    
    # Display books in the competition
    st.subheader("Books")
    for book in competition['books']:
        st.write(book)
    
    # Add Compete button
    if st.button("Compete"):
        st.switch_page("./pages/compete.py")
else:
    st.error("Competition not found")