import streamlit as st


st.set_page_config(page_title="Right on Read", layout="wide")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

login_page = st.Page("pages/login.py", title="Login", icon="🔑")
register_page = st.Page("pages/register.py", title="Register", icon="📝")
profile_page = st.Page("pages/profile.py", title="Profile", icon="👤")
competitions_page = st.Page("pages/competitions.py", title="Competitions", icon="🏆")
competition_detail_page = st.Page("pages/competition_detail.py", title=" ")
read_book_page = st.Page("pages/read_book.py", title="Read Book", icon="📚")
compete_page = st.Page("pages/compete.py", title=" ")


if st.session_state.user:
    pg = st.navigation([profile_page, competitions_page, competition_detail_page, read_book_page, compete_page])
else:
    pg = st.navigation([login_page, register_page])

pg.run()
