import streamlit as st


st.set_page_config(page_title="Right on Read", layout="wide")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

landing_page = st.Page("pages/landing.py", title="Home", icon="🏠")
login_page = st.Page("pages/login.py", title="Login", icon="🔑")
register_page = st.Page("pages/register.py", title=" ")
profile_page = st.Page("pages/profile.py", title="Profile", icon="👤")
competitions_page = st.Page("pages/competitions.py", title="Competitions", icon="🏆")
competition_detail_page = st.Page("pages/competition_detail.py", title=" ")
read_book_page = st.Page("pages/read_book.py", title="Read Book", icon="📚")
compete_page = st.Page("pages/compete.py", title=" ")
create_competition = st.Page("pages/create_competition.py", title="Create Competition", icon="👤")

if st.session_state.user:
    if st.session_state.user["user_type"] == "host":
        pg = st.navigation([landing_page, profile_page, competitions_page, competition_detail_page, read_book_page, create_competition])
    else:
        pg = st.navigation([landing_page, profile_page, competitions_page, competition_detail_page, read_book_page, compete_page])
else:
    pg = st.navigation([login_page, register_page])

pg.run()
