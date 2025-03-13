import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load questions from questions.json
with open("questions.json") as f:
    QUESTIONS = json.load(f)

# Initialize MongoDB connection
@st.cache_resource(ttl=300)
def init_mongo():
    try:
        client = MongoClient(st.secrets["mongo_uri"])
        return client
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

client = init_mongo()

def validate_gmail(email):
    """Ensure Gmail is valid"""
    return email.endswith("@gmail.com")

def get_existing_user(name, email):
    """Check if user with the same Name and Gmail exists in the database"""
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Name": name, "Gmail": email})  # Strict matching
    return None

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # User info section (Name & Gmail)
    st.header("👤 Personal Information")
    name = st.text_input("Full Name", "").strip()
    gmail = st.text_input("Gmail Address", "").strip()

    if st.button("Proceed to Assessment"):
        if not name:
            st.error("❌ Please enter your full name.")
            return
        if not validate_gmail(gmail):
            st.error("❌ Please enter a valid Gmail address (must end with @gmail.com).")
            return

        # Check if the user exists in the database
        existing_user = get_existing_user(name, gmail)
        if not existing_user:
            st.error("❌ User not found! You must enter the **exact same** Name and Gmail used before.")
            return

        # Allow user to continue
        st.session_state["assessment_started"] = True
        st.success("✅ Verified! You can now take the assessment.")

    if "assessment_started" not in st.session_state:
        return  # Stop execution until Name & Gmail are verified

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = st.slider(q["text"], 0, 5)  # Example question type
        
        # Gender selection with validation
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender.")
            return

        if client:
            # Calculate results
            percentage = calculate_health_percentage(responses, QUESTIONS)
            result = get_result_category(percentage)

            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]

                # Save new assessment (but first delete previous record to avoid redundancy)
                collection.delete_one({"Name": name, "Gmail": gmail})

                doc = {
                    "Name": name,
                    "Gmail": gmail,
                    **responses,
                    "Gender": gender.title(),
                    "Health Percentage": percentage,
                    "Results": result,
                    "Assessment date": datetime.now()
                }
                collection.insert_one(doc)
                st.success("✅ Assessment saved successfully!")

                # Show results
                st.subheader("Your Results")
                col1, col2 = st.columns(2)
                col1.metric("Overall Score", f"{percentage:.2f}%")
                col2.metric("Result Category", result)

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
