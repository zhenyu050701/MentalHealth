import streamlit as st
from pymongo import MongoClient

# Retrieve MongoDB connection details from Streamlit secrets
try:
    MONGO_URI = st.secrets["mongo"]["cloud_uri"]  # Change to "local_uri" if using local DB
    DB_NAME = st.secrets["mongo"]["cloud_db"]
    COLLECTION_NAME = st.secrets["mongo"]["cloud_collection"]
except KeyError as e:
    st.error(f"Missing secret: {e}. Please check secrets.toml configuration.")

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    st.success("Connected to MongoDB successfully!")  # For debugging, remove in production
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")

# Function to save assessment data
def save_assessment(user_id, assessment_data):
    """Saves user assessment data to MongoDB."""
    try:
        document = {"user_id": user_id, "assessment": assessment_data}
        collection.insert_one(document)
        return True
    except Exception as e:
        st.error(f"Error saving assessment: {e}")
        return False

# Function to retrieve user assessments
def get_user_assessments(user_id):
    """Retrieves all assessments for a specific user."""
    try:
        assessments = list(collection.find({"user_id": user_id}, {"_id": 0}))
        return assessments
    except Exception as e:
        st.error(f"Error retrieving assessments: {e}")
        return []

