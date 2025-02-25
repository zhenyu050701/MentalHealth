import streamlit as st
from database import save_assessment
from calculation import calculate_health_percentage, get_result_category
import json
import datetime

# Load questions
with open("questions.json", "r") as f:
    questions = json.load(f)

def ask_questions():
    responses = {}
    for question in questions:
        if question["key"] in ["self_harm", "traumatic_event"]:
            # Ensure binary choice (1 = Yes, 0 = No)
            responses[question["key"]] = st.radio(question["text"], [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
        elif question["key"] == "mood":
            # Dropdown selection for mood-related questions
            responses[question["key"]] = st.selectbox(question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"])
        else:
            # Default slider for other questions (0-5)
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)
    return responses

# Streamlit UI
st.title("Mental Health Assessment")

responses = ask_questions()
health_percentage = calculate_health_percentage(responses)
result = get_result_category(health_percentage)

st.write(f"### Your Health Score: {health_percentage}%")
st.write(f"### Result: {result}")

# Save data
assessment = {
    "responses": responses,
    "health_percentage": health_percentage,
    "result": result,
    "assessment_date": datetime.datetime.now().isoformat()
}
save_assessment(assessment)
