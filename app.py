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
    """Connect to MongoDB"""
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
    """Retrieve previous assessment of user"""
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Name": name, "Gmail": email})  # Strict matching
    return None

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # User info section
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

        # Check if the user exists
        existing_user = get_existing_user(name, gmail)
        if not existing_user:
            st.error("❌ User not found! You must enter the **exact same** Name and Gmail used before.")
            return

        # Store previous result for comparison
        st.session_state["previous_result"] = existing_user
        st.session_state["assessment_started"] = True
        st.success("✅ Verified! You can now take the assessment.")

    if "assessment_started" not in st.session_state:
        return  # Stop execution until verification is complete

    # Show previous results
    prev_result = st.session_state.get("previous_result", {})
    if prev_result:
        st.subheader("📊 Your Previous Assessment")
        prev_score = prev_result.get("Health Percentage", 0)
        prev_category = prev_result.get("Results", "Unknown")
        prev_date = prev_result.get("Assessment date", "N/A")

        col1, col2, col3 = st.columns(3)
        col1.metric("Previous Score", f"{prev_score:.2f}%")
        col2.metric("Previous Category", prev_category)
        col3.metric("Date", prev_date)

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = st.slider(q["text"], 0, 5)  # Example question type
        
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender.")
            return

        if client:
            # Calculate results
            new_percentage = calculate_health_percentage(responses, QUESTIONS)
            new_category = get_result_category(new_percentage)

            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]

                # Store previous before overwriting
                prev_score = prev_result.get("Health Percentage", 0)

                # Remove old record and insert new one
                collection.delete_one({"Name": name, "Gmail": gmail})
                doc = {
                    "Name": name,
                    "Gmail": gmail,
                    **responses,
                    "Gender": gender.title(),
                    "Health Percentage": new_percentage,
                    "Results": new_category,
                    "Assessment date": datetime.now()
                }
                collection.insert_one(doc)
                st.success("✅ Assessment saved successfully!")

                # Show new results
                st.subheader("📊 Your New Results")
                col1, col2 = st.columns(2)
                col1.metric("Current Score", f"{new_percentage:.2f}%")
                col2.metric("Result Category", new_category)

                # Compare results
                score_diff = new_percentage - prev_score
                change_msg = "Improved" if score_diff > 0 else "Declined" if score_diff < 0 else "No Change"

                st.subheader("📈 Comparison with Previous Result")
                st.write(f"Your mental health score has **{change_msg}** by **{abs(score_diff):.2f}%**.")
                
                # Show a comparison bar chart
                df = pd.DataFrame({
                    "Assessment": ["Previous", "Current"],
                    "Health Percentage": [prev_score, new_percentage]
                })
                fig = px.bar(df, x="Assessment", y="Health Percentage", text="Health Percentage", 
                             color="Assessment", title="Comparison of Mental Health Score",
                             labels={"Health Percentage": "Score (%)"})
                fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                st.plotly_chart(fig)

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
