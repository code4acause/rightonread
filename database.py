from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import streamlit as st
import certifi
ca = certifi.where()

uri = f"mongodb+srv://{st.secrets["mongo"]["username"]}:{st.secrets["mongo"]["password"]}@cluster0.ssnuihs.mongodb.net/?appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


db = client["reading_competition_db"]


users_collection = db["users"]
competitions_collection = db["competitions"]
books_collection = db["books"]

def confirmConnection():
    try:
        client.admin.command('ping')
        return ("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        return (e)
