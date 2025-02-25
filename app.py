import streamlit as st
import json
import datetime

# Load questions (Make sure questions.json exists and contains your question data)
with open("questions.json", "r") as f:
    questions = json.load(f)

# Total number of questions
total_questions = len(questions)

# Total Marks (100)
total_marks = 100

# Function to calculate marks per question
def calculate_marks_per_question():
    marks_per_question = total_marks / total_questions
    return marks_per_question

# Mood scoring weights (balanced distribution)
mood_scores = {
    "Happy": 1.0,    # Happy gets full marks (1.0)
    "Neutral": 0.8,   # Neutral gets 80% of the marks
    "Anxious": 0.6,   # Anxious gets 60% of the marks
    "Sad": 0.4,       # Sad gets 40% of the marks
    "Depressed": 0.2  # Depressed gets 20% of the marks
}

# Function to ask questions
def ask_questions():
    responses = {}

    # Ask gender first (no scoring)
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    for question in questions:
        if question["key"] == "self_harm":
            responses[question["key"]] = st.radio(question["text"], [0, 1])
        elif question["key"] == "traumatic_event":
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # No=0, Yes=1
        elif question["key"] == "substance_use":
            responses[question["key"]] = st.radio(question["text"], [0, 1])  # No=0, Yes=1
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(
                question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"]
            )
        elif question["key"] in ["work_stress", "anxiety_level", "stress_level"]:
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)
        else:
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)

    return responses

# Function to calculate the mental health percentage
def calculate_health_percentage(responses):
    total_score = 0

    for key, value in responses.items():
        if key in ["traumatic_event", "substance_use"]:
            # For "No" answer (0), give full marks (marks_per_question), for "Yes" (1), give 0 points
            total_score += (1 - value) * calculate_marks_per_question()
        elif key in ["work_stress", "anxiety_level", "stress_level"]:
            # Reverse scale: For 0 = best, give full marks, for 5 = worst, give 0 marks
            total_score += (5 - value) / 5 * calculate_marks_per_question()
        elif key == "mood":
            # Use balanced mood scores
            total_score += mood_scores.get(value, 0) * calculate_marks_per_question()
        elif isinstance(value, int):
            # For other 0-5 scale answers, calculate score proportionally
            total_score += (value / 5) * calculate_marks_per_question()

    return total_score

# Streamlit UI
st.title("Mental Health Assessment")

# Initialize the responses
responses = ask_questions()

# Submit the form
if st.button("Submit Assessment"):
    health_percentage = calculate_health_percentage(responses)
    
    # Ensure the total score is exactly 100
    health_percentage = min(100, max(0, health_percentage))  # Bound the score between 0 and 100
    
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

    # Optionally save this result to a database or file if needed.
