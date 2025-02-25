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
    """Dynamically generates the questionnaire based on JSON data."""
    responses = {}

    # Ask for gender first
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        key = question["key"]
        text = question["text"]

        if key in ["self_harm", "traumatic_event"]:  
            # Binary Yes/No (1 = Yes, 0 = No)
            responses[key] = st.radio(text, [0, 1] if key == "self_harm" else [1, 0])

        elif key == "mood":
            responses[key] = st.selectbox(
                text, ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )

        elif "scale" in question:
            # Questions that use a scale (0-5)
            responses[key] = st.slider(text, 0, 5, 3)

        else:
            # Any other text-based input (if needed in future)
            responses[key] = st.text_input(text, "")

    return responses

def calculate_health_percentage(responses):
    """Calculates the mental health score based on responses."""
    total_score = 0
    max_score = 0

    for key, value in responses.items():
        if key in ["self_harm", "traumatic_event"]:  
            max_score += 1
            total_score += (1 - value) if key == "traumatic_event" else value  
        
        elif isinstance(value, int):  
            total_score += value
            max_score += 5  

    return int((total_score / max_score) * 100) if max_score else 0

def get_result_category(score):
    """Categorizes the mental health score into levels."""
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
