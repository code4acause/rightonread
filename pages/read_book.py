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
# questions_collection = db["questions"]
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



def generate_questions(book_text, book_id):

    prompt = f"""Given the following excerpt of a book, generate 5 general plot questions that would require the reader to flip through the book to find where they happened. Don't include the general location to find the answer to the question. Provide the relevant quote from the text in the answer. Avoid trick questions not directly answerable from the text. Respond in JSON format with an array of question objects, each containing 'question' and 'answer' fields:

    {book_text[:15000]}"""  # OpenAI has a smaller context window, so we're limiting to 4000 characters
    format = "[{\"question\": \"What was the name of the protagonist's childhood pet?\",\"answer\": \"The protagonist's childhood pet was a golden retriever named Sunny. This is evident from the passage: 'I still remember Sunny, my golden retriever, wagging her tail every time I came home from school.'\"},{\"question\": \"In which city did the main character start their career?\",\"answer\": \"The main character started their career in New York City. This is mentioned in the text: 'Fresh out of college, I packed my bags and headed to the bustling streets of New York City, ready to start my first real job.'\"},{\"question\": \"What was the unexpected event that changed the course of the story?\",\"answer\": \"The unexpected event was a letter from a long-lost relative. The text states: 'Just as I was settling into my routine, a letter arrived. Postmarked from a small town I'd never heard of, it was from an aunt I didn't know existed.'\"}]"
    try:
        client = OpenAI(api_key= st.secrets["OPENAI_KEY"])

        response = client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates questions about books in this exact format: {format}"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        st.write(response.choices[0].message)
        st.write("Response:", response.choices[0].message.content.strip()[7:-3:])
        questions_json = json.loads(response.choices[0].message.content.strip()[7:-3:])
        print(questions_json)

        return questions_json

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return []

# def generate_questions(book_text, book_id):
#     model = genai.GenerativeModel(
#         "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
#     )
#     prompt = f"Given the following book text, generate 5 general plot questions that would require the reader to flip through the book to find where they happened. Don't include the general location to find the answer to the question. Provide the relevant quote from the text in the answer. Avoid trick questions not directly answerable from the text. Respond in JSON format with an array of question objects, each containing 'question' and 'answer' fields:\n\n{book_text[:30000]}"
#     response = model.generate_content(
#         prompt,
#         generation_config={"temperature": 0.7},
#         safety_settings=safety
#     )
#     st.write("Response:", response)
#     questions_json = json.loads(response.text)

#     # Store questions in the database
#     # for q in questions_json:
#     #    q["book_id"] = book_id
#     #    questions_collection.insert_one(q)

#     return questions_json


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


def update_user_stats(user_id, correct):
    user_stats = db.user_stats.find_one({"user_id": user_id})
    if user_stats:
        db.user_stats.update_one(
            {"user_id": user_id},
            {"$inc": {"total_questions": 1, "correct_answers": 1 if correct else 0}},
        )
    else:
        db.user_stats.insert_one(
            {
                "user_id": user_id,
                "total_questions": 1,
                "correct_answers": 1 if correct else 0,
            }
        )


st.title("Interactive Book Quiz")

# User authentication (simplified for this example)
user_id = st.session_state.user

if user_id:
    bid = st.query_params.get("book_id") # st.session_state.get("book_id")
    option = st.selectbox("Choose an option:", ["Search for a book", "Upload a PDF"])
    if bid:
        st.write("Book ID:", bid)
        st.write("Book Title:", st.session_state.book_title)
        competition = competitions_collection.find_one({"_id": ObjectId(st.session_state.competition_id)})
        st.write("Competition:", competition)
        book_c = db.pdf_books.find_one({"id": bid})
        if  book_c:
            book_text = book_c["content"]
        #download_book_text(bid)
        st.write("Book Text:", book_text[:1000])
        questions = generate_questions(book_text, 0)
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
    questions = st.session_state.get("questions", [])
    st.write("Answer at least 4 out of 5 questions correctly to pass the quiz")
    quizstatus = [False]*len(questions)
    if questions:
        selected_question = st.selectbox(
            "Select a question:", [q["question"] for q in questions]
        )
        if selected_question:
            selected_question_data = next(
                q for q in questions if q["question"] == selected_question
            )

            answer_method = st.radio("Choose how to answer:", ["Text", "Visual"])

            if answer_method == "Visual":
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
                        #"question_id": selected_question_data["_id"],
                        "correct": analysis["correct"],
                        "confidence": analysis["confidence"],
                        "timestamp": time.time(),
                        "answer_method": "visual",
                    }
                    user_responses_collection.insert_one(user_response)
                    update_user_stats(user_id, analysis["correct"])

            elif answer_method == "Text":
                user_text_answer = st.text_input("Your answer:")
                if st.button("Submit Answer"):
                    analysis = evaluate_text_answer(
                        selected_question,
                        user_text_answer,
                        selected_question_data["answer"],
                    )
                    st.write("Analysis:", analysis)

                    user_response = {
                        "user_id": user_id,
                        "book_id": book_id,
                        "question_id": selected_question_data["_id"],
                        "correct": analysis["correct"],
                        "confidence": analysis["confidence"],
                        "timestamp": time.time(),
                        "answer_method": "text",
                        "user_answer": user_text_answer,
                    }
                    user_responses_collection.insert_one(user_response)
                    update_user_stats(user_id, analysis["correct"])
