import streamlit as st
from database import save_assessment
from calculation import calculate_health_percentage, get_result_category
import json
import datetime
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://Cheng:Cheng12345@frogcluster.bvxnl.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["MentalHealth"]
collection = db["Assessments"]

# Load questions
with open("questions.json", "r") as f:
    questions = json.load(f)

def ask_questions():
    responses = {}

    # Ask for gender
    gender = st.radio("Select your gender:", ["Male", "Female"])
    responses["gender"] = gender

    # Loop through questions
    for question in questions:
        if question["key"] in ["self_harm", "traumatic_event"]:
            responses[question["key"]] = st.radio(question["text"], [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
        elif question["key"] == "mood":
            responses[question["key"]] = st.selectbox(question["text"], ["Neutral", "Happy", "Anxious", "Depressed", "Sad"])
        else:
            responses[question["key"]] = st.slider(question["text"], 0, 5, 3)

    return responses

# Streamlit UI
st.title("Mental Health Assessment")

responses = ask_questions()

# Submit button
if st.button("Submit"):
    health_percentage = calculate_health_percentage(responses)
    result = get_result_category(health_percentage)

    # Display results after pressing Submit
    st.write(f"### Your Health Score: {health_percentage}%")
    st.write(f"### Result: {result}")

    # Save data to MongoDB
    assessment = {
        "responses": responses,
        "health_percentage": health_percentage,
        "result": result,
        "assessment_date": datetime.datetime.now().isoformat()
    }
    collection.insert_one(assessment)
    st.success("Your assessment has been saved successfully!")
