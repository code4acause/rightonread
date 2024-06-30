import streamlit as st
from database import competitions_collection
from utils import check_user_logged_in
import tempfile
import os
from bson import ObjectId
import PyPDF2
from streamlit.runtime.scriptrunner import RerunData, RerunException
import datetime

check_user_logged_in()
st.header("Competitions")

# List existing competitions
competitions = competitions_collection.find()
for comp in competitions:
    st.subheader(comp['name'])
    st.write(comp['description'])
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Join {comp['name']}"):
            competitions_collection.update_one(
                {"_id": comp["_id"]},
                {"$addToSet": {"participants": st.session_state.user["_id"]}}
            )
            st.success(f"Joined {comp['name']} successfully!")
    with col2:
        if st.button(f"View {comp['name']}"):
            st.query_params["id"]=str(comp['_id'])
            # Switch to the competition detail page
            st.switch_page("./pages/competition_detail.py")
            raise RerunException(
                RerunData(
                    page_script_hash=st.runtime.scriptrunner.get_script_run_ctx().page_script_hash,
                    page_name="stpages/competition_detail.py",
                )
            )

# Initialize session state variables if not already set
if "create_competition" not in st.session_state:
    st.session_state.create_competition = False

# Button to start creating competition
if st.button("Create Competition"):
    st.session_state.create_competition = True

# Display form fields only if the competition creation is initiated
if st.session_state.create_competition:
    with st.form("a"):
        name = st.text_input("Competition Name")
        description = st.text_area("Description")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        books = st.file_uploader("Upload Books (PDF)", accept_multiple_files=True, type="pdf")
        print("AAA")
        submitted = st.form_submit_button("Create")
        if submitted:
            print("DONE")
            book_names = []
            raw_texts = {}  # Dictionary to store raw text with filename as key
            for book in books:
                print("CCC")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(book.getvalue())
                    book_names.append(os.path.basename(book.name))
                    tmp_file.close()  # Close the temporary file before processing
                    
                    # Extract text from PDF
                    pdf_file = open(tmp_file.name, 'rb')
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ''
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    pdf_file.close()
                    
                    # Store text in dictionary with filename as key
                    raw_texts[os.path.basename(book.name)] = text
                    
            # Create new_competition object with raw_texts included
            new_competition = {
                "name": name,
                "description": description,
                "start_date": datetime.datetime.combine(start_date, datetime.time.min),
                "end_date": datetime.datetime.combine(end_date, datetime.time.min),
                "books": book_names,
                "raw_texts": raw_texts,  # Include raw_texts in the competition data
                "participants": [st.session_state.user["_id"]],
                "creator": st.session_state.user["_id"]
            }
            
            st.session_state.create_competition=False
            result = competitions_collection.insert_one(new_competition)
            st.query_params["id"]= (str(result.inserted_id))
            raise RerunException(
                RerunData(
                    page_script_hash=st.runtime.scriptrunner.get_script_run_ctx().page_script_hash,
                    page_name="stpages/competition_detail.py",
                )
            )

