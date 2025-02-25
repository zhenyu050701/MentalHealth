import streamlit as st
import json

# Sample questions JSON (replace with actual file loading)
questions = [
    {"key": "traumatic_event", "text": "Have you experienced a recent traumatic event?"},
    {"key": "self_harm", "text": "Have you had thoughts of self-harm?"},
    {"key": "mood", "text": "How would you describe your current mood?"},
    {"key": "anxiety", "text": "How anxious have you felt recently? (0 = Not at all, 5 = Extremely)"},
    {"key": "sleep_quality", "text": "How well have you been sleeping? (0 = Very poor, 5 = Very good)"}
]

def ask_questions():
    responses = {}

    # Ask for gender first
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        key = question["key"]
        
        if key in ["traumatic_event", "self_harm"]:  
            # Use radio buttons for Yes/No questions
            responses[key] = st.radio(question["text"], ["No", "Yes"])
        
        elif key == "mood":
            responses[key] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        else:
            # Use slider for other questions (0 to 5 scale)
            responses[key] = st.slider(question["text"], 0, 5, 3)

    return responses

# Streamlit UI
st.title("Mental Health Assessment")
responses = ask_questions()

if st.button("Submit Assessment"):
    st.write("Responses:", responses)
