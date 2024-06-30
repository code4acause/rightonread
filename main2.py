import streamlit as st
from bson import ObjectId

st.session_state.user = {'_id': ObjectId('6680c9e29c8d24f1cc1462df'), 'username': 'darrenweng', 'bio': '', 'user_type': 'user'}
st.write("Test Page!")

if st.button("Test Profile"):
    st.query_params["view_id"] = "123"
    st.switch_page("pages/profile.py")