import streamlit as st
from pymongo import MongoClient

# Load MongoDB credentials from Streamlit secrets
MONGO_URI = st.secrets["mongo_uri"]
DB_NAME = st.secrets["db_name"]
COLLECTION_NAME = st.secrets["collection_name"]

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def save_assessment(assessment_data):
    """Save assessment data to MongoDB."""
    try:
        collection.insert_one(assessment_data)
        return True
    except Exception as e:
        st.error(f"Error saving assessment: {e}")
        return False

def get_assessments():
    """Retrieve all assessments from MongoDB."""
    try:
        return list(collection.find({}, {"_id": 0}))  # Exclude MongoDB object ID
    except Exception as e:
        st.error(f"Error fetching assessments: {e}")
        return []

def delete_assessment(filter_query):
    """Delete an assessment from MongoDB based on a filter."""
    try:
        result = collection.delete_one(filter_query)
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Error deleting assessment: {e}")
        return False
