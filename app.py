import streamlit as st
from pymongo import MongoClient
import plotly.express as px  # For pie chart
import json
import datetime

# Load MongoDB credentials from Streamlit secrets
MONGO_URI = st.secrets["mongo_uri"]
DB_NAME = st.secrets["db_name"]
COLLECTION_NAME = st.secrets["collection_name"]

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Load questions
with open("questions.json", "r") as f:
    questions = json.load(f)

def ask_questions():
    responses = {}

    # Ask for gender first
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        if question["key"] == "self_harm":
            # Binary choice (0 = No, 1 = Yes)
            responses[question["key"]] = st.radio(question["text"], [0, 1])
        elif question["key"] == "traumatic_event":
            # Ensure traumatic_event follows 1-0 format (1 = Yes, 0 = No)
            responses[question["key"]] = st.radio(question["text"], [1, 0])
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        else:
            # Use slider for other questions (0 to 5 scale)
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)

    return responses

def calculate_health_percentage(responses):
    """Calculates the mental health score based on responses"""
    total_score = 0
    max_score = 0
    
    for key, value in responses.items():
        if key == "self_harm":  
            max_score += 1  # Binary scale (0-1)
        elif key == "traumatic_event":
            max_score += 1  # Binary but in 1-0 format
            total_score += 1 - value  # Convert 1-0 to a normal scoring system
        elif isinstance(value, int):  
            total_score += value
            max_score += 5  # Assuming each question is on a 0-5 scale

    if max_score == 0:
        return 0  # Avoid division by zero

    return int((total_score / max_score) * 100)

def get_result_category(score):
    """Categorizes the mental health score into levels"""
    if score < 20:
        return "Severe Risk"
    elif score < 40:
        return "High Risk"
    elif score < 60:
        return "Moderate Risk"
    elif score < 80:
        return "Mild Risk"
    else:
        return "Healthy"

# Streamlit UI
st.title("Mental Health Assessment")

if "submitted" not in st.session_state:
    st.session_state.submitted = False

responses = ask_questions()

if st.button("Submit Assessment"):
    health_percentage = calculate_health_percentage(responses)
    result = get_result_category(health_percentage)

    assessment = {
        "responses": responses,
        "health_percentage": health_percentage,
        "result": result,
        "assessment_date": datetime.datetime.now().isoformat()
    }

    if collection.insert_one(assessment):
        st.session_state.submitted = True

if st.session_state.submitted:
    st.write(f"### Your Health Score: {health_percentage}%")
    st.write(f"### Result: {result}")

    # Fetch all assessments and create a pie chart
    assessments = list(collection.find({}, {"_id": 0, "health_percentage": 1}))
    score_ranges = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}

    for a in assessments:
        score = a["health_percentage"]
        if 0 <= score < 20:
            score_ranges["0-20"] += 1
        elif 20 <= score < 40:
            score_ranges["20-40"] += 1
        elif 40 <= score < 60:
            score_ranges["40-60"] += 1
        elif 60 <= score < 80:
            score_ranges["60-80"] += 1
        else:
            score_ranges["80-100"] += 1

    fig = px.pie(
        names=list(score_ranges.keys()),
        values=list(score_ranges.values()),
        title="Health Score Distribution"
    )
    st.plotly_chart(fig)  
