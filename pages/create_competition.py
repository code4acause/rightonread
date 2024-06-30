import streamlit as st
import requests
from database import db, competitions_collection
from datetime import datetime, timedelta
from bson import ObjectId
from PyPDF2 import PdfReader
import hashlib

def search_books(query):
    response = requests.get(f"https://gutendex.com/books?search={query}")
    return response.json()['results']

def download_book_text(book_id):
    book_info = requests.get(
        f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    ).text
    return book_info

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_author_names(author_data):
    if isinstance(author_data, list):
        return [author.get('name', 'Unknown') for author in author_data]
    elif isinstance(author_data, dict):
        return [author_data.get('name', 'Unknown')]
    else:
        return ['Unknown']

st.title("Create Competition")

# Initialize session state for selected books
if 'selected_books' not in st.session_state:
    st.session_state.selected_books = []

# Competition details form
with st.form("competition_details"):
    competition_name = st.text_input("Competition Name")
    description = st.text_area("Description")
    start_date = st.date_input("Start Date", min_value=datetime.now())
    end_date = st.date_input("End Date", min_value=start_date + timedelta(days=1))
    submit_details = st.form_submit_button("Save Details")

if submit_details:
    st.success("Competition details saved. Now add books to your competition.")

# Book search and add functionality
st.subheader("Add Books to Competition")
option = st.selectbox("Choose an option:", ["Search for a book", "Upload a PDF"])

if option == "Search for a book":
    search_query = st.text_input("Search for a book:")
    if search_query:
        books = search_books(search_query)
        if not books:
            st.write("No books found. Please try another search query.")
        else:
            for book in books:
                col1, col2 = st.columns([3, 1])
                with col1:
                    authors = get_author_names(book.get('authors', []))
                    st.write(f"{book.get('title', 'Unknown Title')} by {', '.join(authors)}")
                with col2:
                    if st.button("Add", key=f"add_{book.get('id', '')}"):
                        book_text = download_book_text(book.get('id', ''))
                        book_info = {
                            "id": str(book.get('id', '')),
                            "title": book.get('title', 'Unknown Title'),
                            "authors": authors,
                            "content": book_text,
                            "type": "gutenberg"
                        }
                        if book_info not in st.session_state.selected_books:
                            st.session_state.selected_books.append(book_info)
                            st.success(f"Added: {book_info['title']}")
                        else:
                            st.warning(f"{book_info['title']} is already in the competition.")

elif option == "Upload a PDF":
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file is not None:
        book_text = extract_text_from_pdf(uploaded_file)
        pdf_hash = hashlib.md5(book_text.encode()).hexdigest()
        
        book_info = {
            "id": pdf_hash,
            "title": uploaded_file.name,
            "authors": ["Unknown"],
            "type": "pdf",
            "content": book_text
        }
        
        if st.button("Add PDF to Competition"):
            if book_info not in st.session_state.selected_books:
                st.session_state.selected_books.append(book_info)
                st.success(f"Added: {uploaded_file.name}")
            else:
                st.warning(f"{uploaded_file.name} is already in the competition.")

# Display and remove selected books
st.subheader("Selected Books")
for i, book in enumerate(st.session_state.selected_books):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{book['title']} by {', '.join(book['authors'])} ({book['type']})")
    with col2:
        if st.button("Remove", key=f"remove_{i}"):
            st.session_state.selected_books.pop(i)
            st.rerun()

# Create competition button
if st.button("Create Competition"):
    if not competition_name or not description or not st.session_state.selected_books:
        st.error("Please fill in all details and add at least one book to the competition.")
    else:
        new_competition = {
            "name": competition_name,
            "description": description,
            "start_date": datetime.combine(start_date, datetime.min.time()),
            "end_date": datetime.combine(end_date, datetime.min.time()),
            "books": [
                {
                    "id": book['id'],
                    "title": book['title'],
                    "authors": book['authors'],
                    "type": book['type']
                } for book in st.session_state.selected_books
            ],
            "creator": st.session_state.user["_id"],
            "participants": [st.session_state.user["_id"]],
            "created_at": datetime.now()
        }
        
        # Store PDF content separately
        for book in st.session_state.selected_books:
            #if book['type'] == 'pdf':
            db.pdf_books.insert_one({
                "id": book['id'],
                "content": book['content']
            })
        
        result = competitions_collection.insert_one(new_competition)
        if result.inserted_id:
            st.success("Competition created successfully!")
            st.session_state.selected_books = []  # Clear selected books
        else:
            st.error("Failed to create competition. Please try again.")