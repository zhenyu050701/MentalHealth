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

# Define questions
questions = [
    {"key": "self_harm", "text": "Have you engaged in self-harm? (0 = No, 1 = Yes)"},
    {"key": "traumatic_event", "text": "Have you experienced a recent traumatic event? (0 = No, 1 = Yes)"},
    {"key": "concentration", "text": "Rate your concentration level (0-5)"},
    {"key": "mood", "text": "How would you describe your current mood?"},
]

def ask_questions():
    """Displays questions and collects responses."""
    responses = {}

    # Ask for gender first
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        if question["key"] in ["self_harm", "traumatic_event"]:
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # Radio button (0 or 1)
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        else:
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)  # Slider for numeric response

    return responses

def save_assessment(assessment_data):
    """Save assessment data to MongoDB."""
    try:
        collection.insert_one(assessment_data)
        return True
    except Exception as e:
        st.error(f"Error saving assessment: {e}")
        return False

# Streamlit UI
st.title("Mental Health Assessment")

# Collect responses
assessment_data = ask_questions()

# Submit button
if st.button("Submit Assessment"):
    if save_assessment(assessment_data):
        st.success("Assessment saved successfully!")
    else:
        st.error("Failed to save assessment.")
