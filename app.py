import streamlit as st
from database import save_assessment
from calculation import calculate_health_percentage, get_result_category
import json
import datetime

# Load questions
with open("questions.json", "r") as f:
    questions = json.load(f)

# Mood mapping for numeric scores
MOOD_SCORES = {
    "Neutral": 3,
    "Happy": 5,
    "Anxious": 2,
    "Depressed": 1,
    "Sad": 2
}

def ask_questions():
    responses = {}

    # Gender selection (not included in calculations)
    responses["gender"] = st.radio("Select your gender:", ["Male", "Female"])

    # Loop through questions
    for question in questions:
        key = question["key"]

        if key in ["self_harm", "traumatic_event"]:
            responses[key] = st.radio(question["text"], [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
        
        elif key == "mood":
            mood_choice = st.selectbox(question["text"], list(MOOD_SCORES.keys()))
            responses[key] = MOOD_SCORES[mood_choice]  # Convert to numeric value
        
        else:
            responses[key] = st.slider(question["text"], 0, 5, 3)  # Always numeric

    return responses

# Streamlit UI
st.title("Mental Health Assessment")

# Ask for user input
responses = ask_questions()

# Submit button to display results
if st.button("Submit Assessment"):
    # Filter only numeric values for calculation
    numeric_responses = {k: v for k, v in responses.items() if isinstance(v, (int, float))}
    
    health_percentage = calculate_health_percentage(numeric_responses)  # Now only numbers
    result = get_result_category(health_percentage)

    st.write(f"### Your Health Score: {health_percentage}%")
    st.write(f"### Result: {result}")

    # Save data to MongoDB (store full responses, but only calculate from numeric ones)
    assessment = {
        "responses": responses,  # Save all user inputs
        "health_percentage": health_percentage,
        "result": result,
        "assessment_date": datetime.datetime.now().isoformat()
    }
    save_assessment(assessment)
    st.success("Your assessment has been saved successfully.")
