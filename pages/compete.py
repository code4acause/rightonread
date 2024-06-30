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
    st.header(f"Compete in {competition['name']}")
    
    # Display current user's progress
    user = users_collection.find_one({"_id": st.session_state.user["_id"]})
    books_read = user.get('books_read', {}).get(str(competition['_id']), [])
    st.write(f"You have read {len(books_read)} out of {len(competition['books'])} books.")
    
    # Display list of books with checkboxes
    st.subheader("Books")
    for book in competition['books']:
        is_read = book in books_read
        if st.checkbox(book, value=is_read, key=f"book_{book}"):
            if book not in books_read:
                books_read.append(book)
        else:
            if book in books_read:
                books_read.remove(book)
    
    # Update user's progress
    if st.button("Update Progress"):
        users_collection.update_one(
            {"_id": st.session_state.user["_id"]},
            {"$set": {f"books_read.{str(competition['_id'])}": books_read}}
        )
        st.success("Progress updated successfully!")
        st.experimental_rerun()
else:
    st.error("Competition not found")