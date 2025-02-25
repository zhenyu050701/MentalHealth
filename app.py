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

def calculate_health_percentage(responses):
    """
    Calculates a health percentage score based on responses.
    Adjust this logic as needed.
    """
    total_score = 0
    count = 0

    for key, value in responses.items():
        if key in ["self_harm", "traumatic_event"]:
            total_score += value * 20  # Assign weight to 0-1 questions
        elif isinstance(value, int):  # Ensure it's a numerical value (slider)
            total_score += value * 10  # Assign weight to 0-5 scale
        count += 1

    return min(100, (total_score / (count * 10)) * 100)  # Normalize to 100%

def get_result_category(health_percentage):
    """
    Categorizes health percentage into result categories.
    """
    if health_percentage < 20:
        return "Severe Mental Distress"
    elif 20 <= health_percentage < 40:
        return "Moderate Mental Distress"
    elif 40 <= health_percentage < 60:
        return "Mild Mental Distress"
    elif 60 <= health_percentage < 80:
        return "Generally Stable"
    else:
        return "Mentally Healthy"

def ask_questions():
    """
    Generates the mental health questionnaire UI.
    """
    responses = {}

    # Ask for gender first
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        if question["key"] in ["self_harm", "traumatic_event"]:
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # Only 0 and 1
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        else:
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)

    return responses

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

    try:
        collection.insert_one(assessment)
        st.session_state.submitted = True
    except Exception as e:
        st.error(f"Error saving data: {e}")

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
