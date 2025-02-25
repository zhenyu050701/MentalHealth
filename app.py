import streamlit as st
import json
import datetime
from pymongo import MongoClient


# Define the weight for the 0-5 scale questions
weight = 6.67  # Marks per question

# Load questions (Make sure questions.json exists and contains your question data)
with open("questions.json", "r") as f:
    questions = json.load(f)

# Function to ask questions
def ask_questions():
    responses = {}

    # Ask gender first (no scoring)
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        if question["key"] == "self_harm":
            # Binary choice (0 = No, 1 = Yes)
            responses[question["key"]] = st.radio(question["text"], [0, 1])
        elif question["key"] == "traumatic_event":
            # Yes/No options for traumatic event (0 = No, 1 = Yes)
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # No=0, Yes=1
        elif question["key"] == "substance_use":
            # Yes/No options for substance use (0 = No, 1 = Yes)
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # No=0, Yes=1
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        else:
            # Use slider for other questions (0 to 5 scale)
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)

    return responses

# Calculate the mental health percentage
def calculate_health_percentage(responses):
    total_score = 0

    for key, value in responses.items():
        if key in ["traumatic_event", "substance_use"]:
            # For "No" answer (0), give 6.67 points, for "Yes" (1), give 0 points
            total_score += value * -weight + weight  # If value is 0, it gives weight, if 1, it gives 0
        elif isinstance(value, int):
            # For other 0-5 scale answers, calculate score proportionally
            total_score += (value / 5) * weight

    return total_score

# Streamlit UI
st.title("Mental Health Assessment")

# Initialize the responses
responses = ask_questions()

# Submit the form
if st.button("Submit Assessment"):
    health_percentage = calculate_health_percentage(responses)
    
    # Calculate the result category
    if health_percentage < 20:
        result = "Severe Risk"
    elif health_percentage < 40:
        result = "High Risk"
    elif health_percentage < 60:
        result = "Moderate Risk"
    elif health_percentage < 80:
        result = "Mild Risk"
    else:
        result = "Healthy"

    # Record the assessment with responses and result
    assessment = {
        "responses": responses,
        "health_percentage": health_percentage,
        "result": result,
        "assessment_date": datetime.datetime.now().isoformat()
    }

    # Display the result
    st.write(f"### Your Health Score: {health_percentage:.2f}%")
    st.write(f"### Result: {result}")

    # You can also save this result to a database or file if needed.
