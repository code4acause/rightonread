import streamlit as st
from database import competitions_collection, users_collection
from utils import check_user_logged_in
from bson import ObjectId

check_user_logged_in()

# Get competition ID from query params or session state
competition_id = st.query_params.get("id") or st.session_state.get("competition_id")

if not competition_id:
    st.error("No competition ID provided")
    st.stop()

# Store competition ID in session state
st.session_state.competition_id = competition_id

competition = competitions_collection.find_one({"_id": ObjectId(competition_id)})
if competition:
    st.header(competition['name'])
    st.write(competition['description'])
    st.write(f"Start Date: {competition['start_date'].date()}")
    st.write(f"End Date: {competition['end_date'].date()}")
    
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
        col1, col2 = st.columns(2)
        col1.write(book["title"])
        with col2:
            if st.button(f"Read", key=f"read_{book['id']}"):
                st.query_params["book_id"] = book['id']
                st.session_state.book_id = book['id']
                st.session_state.book_title = book['title']
                st.session_state.competition_id = competition_id
                st.switch_page("pages/read_book.py")
    
    # Add Compete button
    if st.button("Compete"):
        st.session_state.competition_id = competition_id
        st.switch_page("pages/compete.py")
else:
    st.error("Competition not found")