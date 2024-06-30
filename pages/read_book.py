import streamlit as st
import google.generativeai as genai
from database import db
import requests
import time
import json
from PIL import Image
from PyPDF2 import PdfReader

genai.configure(api_key=st.secrets["google_key"])

# Assume these collections exist in the database
books_collection = db["books"]
questions_collection = db["questions"]
user_responses_collection = db["user_responses"]

def search_books(query):
    response = requests.get(f"https://gutendex.com/books?search={query}")
    return response.json()['results']

def download_book_text(book_id):
    book_info = requests.get(f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt").text
    return book_info

def generate_questions(book_text, book_id):
    model = genai.GenerativeModel('gemini-1.5-pro', generation_config={"response_mime_type": "application/json"})
    prompt = f"Given the following book text, generate 5 general plot questions that would require the reader to flip through the book to find where they happened. Don't include the general location to find the answer to the question. Respond in JSON format with an array of question objects, each containing 'question' and 'answer' fields:\n\n{book_text[:30000]}"
    response = model.generate_content(prompt, generation_config={"temperature": 0.7})
    
    questions_json = json.loads(response.text)
    
    # Store questions in the database
    for q in questions_json:
        q['book_id'] = book_id
        questions_collection.insert_one(q)
    
    return questions_json

def analyze_image(image, question):
    model = genai.GenerativeModel('gemini-1.5-pro', generation_config={"response_mime_type": "application/json"})
    prompt = f"Given the following image and question, determine if the user has flipped to the correct place in the book. If it's obviously not a book or a digital copy of a book, say no. If it's indeterminate from the framing of the picture, please state so. Respond in JSON format with 'correct' (boolean), 'confidence' (float 0-1), and 'explanation' (string) fields. Question: {question}"
    response = model.generate_content([prompt, image], generation_config={"temperature": 0.2})
    return json.loads(response.text)

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

st.title("Interactive Book Quiz")

# User authentication (simplified for this example)
user_id = st.session_state.user

if user_id:
    option = st.selectbox("Choose an option:", ["Search for a book", "Upload a PDF"])
    
    if option == "Search for a book":
        search_query = st.text_input("Search for a book:")
        if search_query:
            books = search_books(search_query)
            if not books:
                st.write("No books found. Please try another search query.")
                st.stop()
            selected_book = st.selectbox("Select a book:", [f"{book['title']}" for book in books])
            selected_book_index = [f"{book['title']}" for book in books].index(selected_book)
            selected_book_data = books[selected_book_index]

            # Store or update book in the database
            book_in_db = books_collection.find_one({"gutenberg_id": selected_book_data['id']})
            if not book_in_db:
                book_doc = {
                    "gutenberg_id": selected_book_data['id'],
                    "title": selected_book_data['title'],
                }
                result = books_collection.insert_one(book_doc)
                book_id = result.inserted_id
            else:
                book_id = book_in_db['_id']

            if st.button("Generate Questions"):
                book_text = download_book_text(selected_book_data['id'])
                questions = generate_questions(book_text, book_id)

                # Store questions in session state
                st.session_state.questions = questions

    elif option == "Upload a PDF":
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded_file is not None:
            book_text = extract_text_from_pdf(uploaded_file)
            
            # Store or update book in the database
            book_doc = {
                "title": uploaded_file.name,
            }
            result = books_collection.insert_one(book_doc)
            book_id = result.inserted_id
            
            if st.button("Generate Questions"):
                questions = generate_questions(book_text, book_id)
                
                # Store questions in session state
                st.session_state.questions = questions

    # Retrieve questions from session state
    questions = st.session_state.get('questions', [])
    
    if questions:
        selected_question = st.selectbox("Select a question:", [q['question'] for q in questions])
        if (selected_question):
            selected_question_data = next(q for q in questions if q['question'] == selected_question)
            captured_image = st.camera_input("Show the book location!")
            if captured_image is not None:
                st.image(captured_image, caption="Captured Image")

                # Analyze image
                image_pil = Image.open(captured_image)
                analysis = analyze_image(image_pil, selected_question)
                st.write("Analysis:", analysis)

                user_response = {
                    "user_id": user_id,
                    "book_id": book_id,
                    "question_id": selected_question_data['_id'],
                    "correct": analysis['correct'],
                    "confidence": analysis['confidence'],
                    "timestamp": time.time()
                }
                user_responses_collection.insert_one(user_response)

                # Update user statistics
                user_stats = db.user_stats.find_one({"user_id": user_id})
                if user_stats:
                    db.user_stats.update_one(
                        {"user_id": user_id},
                        {"$inc": {"total_questions": 1, "correct_answers": 1 if analysis['correct'] else 0}}
                    )
                else:
                    db.user_stats.insert_one({
                        "user_id": user_id,
                        "total_questions": 1,
                        "correct_answers": 1 if analysis['correct'] else 0
                    })
