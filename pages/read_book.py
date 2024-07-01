import streamlit as st
import google.generativeai as genai
from database import db, competitions_collection
import requests
import time
import json
from PIL import Image
from PyPDF2 import PdfReader
from bson import ObjectId
from openai import OpenAI

genai.configure(api_key=st.secrets["google_key"])

# Assume these collections exist in the database
books_collection = db["books"]
user_responses_collection = db["user_responses"]

def search_books(query):
    response = requests.get(f"https://gutendex.com/books?search={query}")
    return response.json()["results"]

def download_book_text(book_id):
    book_info = requests.get(
        f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    ).text
    return book_info

# Disable most safety ratings for debugging purposes
safety = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

def generate_questions(book_text):
    prompt = f"""Given the following excerpt of a book, generate 5 general plot questions that would require the reader to flip through the book to find where they happened. Don't include the general location to find the answer to the question. Provide the relevant quote from the text in the answer. Avoid trick questions not directly answerable from the text. Respond in JSON format with an array of question objects, each containing 'question' and 'answer' fields:

    {book_text[:15000]}"""
    format = "[{\"question\": \"What was the name of the protagonist's childhood pet?\",\"answer\": \"The protagonist's childhood pet was a golden retriever named Sunny. This is evident from the passage: 'I still remember Sunny, my golden retriever, wagging her tail every time I came home from school.'\"},{\"question\": \"In which city did the main character start their career?\",\"answer\": \"The main character started their career in New York City. This is mentioned in the text: 'Fresh out of college, I packed my bags and headed to the bustling streets of New York City, ready to start my first real job.'\"},{\"question\": \"What was the unexpected event that changed the course of the story?\",\"answer\": \"The unexpected event was a letter from a long-lost relative. The text states: 'Just as I was settling into my routine, a letter arrived. Postmarked from a small town I'd never heard of, it was from an aunt I didn't know existed.'\"}]"
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_KEY"])

        response = client.chat.completions.create(
        model="gpt-4",
        messages = [
            {"role": "system", "content": f"You are a helpful assistant that generates questions about books in this exact format: {format}"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        print(response.choices[0].message)
        print("Response:", response.choices[0].message.content.strip())
        questions_json = json.loads(response.choices[0].message.content.strip())
        print(questions_json)

        return questions_json

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return []

def analyze_image(image, question):
    model = genai.GenerativeModel(
        "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
    )
    prompt = f"Given the following image and question, determine if the user has flipped to the correct place in the book. If it's obviously not a book or a digital copy of a book, say no. If it's indeterminate from the framing of the picture, please state so. Respond in JSON format with 'correct' (boolean), 'confidence' (float 0-1), and 'explanation' (string) fields. Question: {question}"
    response = model.generate_content(
        [prompt, image], generation_config={"temperature": 0.2}, safety_settings=safety
    )
    return json.loads(response.text)

def evaluate_text_answer(question, user_answer, correct_answer):
    model = genai.GenerativeModel(
        "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
    )
    prompt = f"Given the following question, user's answer, and correct answer, determine if the user's answer is predominantly correct in substance (indicating that the user has most likely read the book and understands its meaning). Respond in JSON format with 'correct' (boolean), 'confidence' (float 0-1), and 'explanation' (string) fields.\n\nQuestion: {question}\nUser's Answer: {user_answer}\nCorrect Answer: {correct_answer}"
    response = model.generate_content(prompt, generation_config={"temperature": 0.2}, safety_settings=safety)
    return json.loads(response.text)

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def update_question_counters(user_id, correct):
    user = db.users.find_one({"_id": user_id})
    if user:
        update_query = {
            "$inc": {
                "total_questions": 1,
                "correct_answers": 1 if correct else 0,
                "incorrect_answers": 0 if correct else 1
            }
        }
        db.users.update_one({"_id": user_id}, update_query)
    else:
        db.users.insert_one({
            "_id": user_id,
            "total_questions": 1,
            "correct_answers": 1 if correct else 0,
            "incorrect_answers": 0 if correct else 1,
            "books_read": []
        })

def update_books_read(user_id, correct, book_id, book_title):
    if correct:
        user = db.users.find_one({"_id": user_id})
        if user:
            if book_id not in [book['id'] for book in user.get('books_read', [])]:
                update_query = {
                    "$push": {
                        "books_read": {
                            "id": book_id,
                            "title": book_title
                        }
                    }
                }
                db.users.update_one({"_id": user_id}, update_query)
        else:
            db.users.insert_one({
                "_id": user_id,
                "total_questions": 0,
                "correct_answers": 0,
                "incorrect_answers": 0,
                "books_read": [{"id": book_id, "title": book_title}]
            })



st.title("Interactive Book Quiz")

# User authentication (simplified for this example)
user_id = st.session_state.user

if user_id:
    bid = st.query_params.get("book_id")
    option = st.selectbox("Choose an option:", ["Search for a book", "Upload a PDF"])
    if bid:
        st.write("Book ID:", bid)
        st.write("Book Title:", st.session_state.book_title)
        competition = competitions_collection.find_one({"_id": ObjectId(st.session_state.competition_id)})
        #st.write("Competition:", competition)
        book_c = db.pdf_books.find_one({"id": bid})
        if book_c:
            book_text = book_c["content"]
        #st.write("Book Text:", book_text[:1000])
        questions = generate_questions(book_text)
        st.session_state.questions = questions
    elif option == "Search for a book":
        search_query = st.text_input("Search for a book:")
        if search_query:
            books = search_books(search_query)
            if not books:
                st.write("No books found. Please try another search query.")
                st.stop()
            selected_book = st.selectbox(
                "Select a book:", [f"{book['title']}" for book in books]
            )
            selected_book_index = [f"{book['title']}" for book in books].index(
                selected_book
            )
            selected_book_data = books[selected_book_index]

            # Store or update book in the database
            book_in_db = books_collection.find_one(
                {"gutenberg_id": selected_book_data["id"]}
            )
            if not book_in_db:
                book_doc = {
                    "gutenberg_id": selected_book_data["id"],
                    "title": selected_book_data["title"],
                }
                result = books_collection.insert_one(book_doc)
                book_id = result.inserted_id
            else:
                book_id = book_in_db["_id"]

            if st.button("Generate Questions"):
                book_text = download_book_text(selected_book_data["id"])
                questions = generate_questions(book_text)

                # Store questions in session state
                st.session_state.questions = questions
                st.session_state.book_id = book_id
                print(type(book_id))
                st.session_state.book_title = selected_book_data["title"]

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
                questions = generate_questions(book_text)

                # Store questions in session state
                st.session_state.questions = questions
                st.session_state.book_id = book_id
                st.session_state.book_title = uploaded_file.name


    questions = st.session_state.get("questions", [])
    
    if questions:
            #if "question_attempts" not in st.session_state:
        st.session_state.question_attempts = [0] * len(st.session_state.get("questions", []))
   # if "question_status" not in st.session_state:
        st.session_state.question_status = [False] * len(st.session_state.get("questions", []))
        st.write("Answer these questions")
        
        for i, question in enumerate(questions):
            st.subheader(f"Question {i+1}: {question['question']}")

            if st.session_state.question_status[i]:
                st.success("Correct!")
                continue

            if st.session_state.question_attempts[i] >= 3:
                st.error("No more attempts left.")
                continue

            answer_method = st.radio(f"Choose how to answer Question {i+1}:", ["Text", "Visual"], key=f"method_{i}")

            if answer_method == "Visual":
                captured_image = st.camera_input(f"Show the book location for Question {i+1}!")
                if captured_image is not None:
                    st.image(captured_image, caption="Captured Image")
            elif answer_method == "Text":
                st.session_state[f"answer_{i}"] = st.text_input(f"Your answer for Question {i+1}:", key=f"answer_input_{i}")

        submitted = st.button("Submit Answers")

        if submitted:
            for i, question in enumerate(questions):
                if not st.session_state.question_status[i] and st.session_state.question_attempts[i] < 3:
                    st.session_state.question_attempts[i] += 1
                    if st.session_state[f"method_{i}"] == "Visual":
                        captured_image = st.session_state.get(f"Show the book location for Question {i+1}!")
                        if captured_image:
                            image_pil = Image.open(captured_image)
                            analysis = analyze_image(image_pil, question['question'])
                            if analysis['correct']:
                                st.success(f"Question {i+1}: Correct!")
                                st.session_state.question_status[i] = True
                            else:
                                st.error(f"Question {i+1}: Incorrect. Attempts left: {3 - st.session_state.question_attempts[i]}")
                    else:
                        user_answer = st.session_state.get(f"answer_{i}", "")
                        analysis = evaluate_text_answer(question['question'], user_answer, question['answer'])
                        if analysis['correct']:
                            st.success(f"Question {i+1}: Correct!")
                            st.session_state.question_status[i] = True
                        else:
                            st.error(f"Question {i+1}: Incorrect. Attempts left: {3 - st.session_state.question_attempts[i]}")
                    
                    update_question_counters(user_id, analysis['correct'])  
            print(st.session_state.question_status)
            st.session_state.question_status= st.session_state.question_status

        if st.button("Finish Quiz"):
            print(st.session_state.question_status)
            correct_count = sum(st.session_state.question_status)
            st.write(f"Quiz completed! You answered {correct_count} out of {len(questions)} questions correctly.")
            
            if correct_count >= 4:
                update_books_read(user_id, st.session_state.book_id, st.session_state.book_title)
                st.success("Congratulations! You passed the quiz.")
            else:
                st.warning("You didn't pass the quiz. Keep reading and try again!")

            # Reset quiz state
            st.session_state.question_attempts = [0] * len(questions)
            st.session_state.question_status = [False] * len(questions)
        

    else:
        st.write("No questions available. Please generate questions first.")