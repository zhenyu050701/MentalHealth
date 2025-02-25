import streamlit as st
from pymongo import MongoClient

# Load MongoDB secrets
MONGO_URI = st.secrets["mongo_uri"]
DB_NAME = st.secrets["db_name"]
COLLECTION_NAME = st.secrets["collection_name"]

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def save_assessment(user_id, assessment_data):
    """Saves user assessment data to MongoDB."""
    try:
        document = {"user_id": user_id, "assessment": assessment_data}
        collection.insert_one(document)
        return True
    except Exception as e:
        st.error(f"Error saving assessment: {e}")
        return False
