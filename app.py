import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load questions configuration
with open("questions.json") as f:
    QUESTIONS = json.load(f)

# MongoDB connection
@st.cache_resource(ttl=300)
def init_mongo():
    try:
        client = MongoClient(st.secrets["mongo_uri"])
        return client
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

client = init_mongo()

def fetch_latest_assessment(gmail):
    """Retrieve the latest assessment for a given Gmail"""
    if not client:
        return None
    
    db = client[st.secrets["db_name"]]
    collection = db[st.secrets["collection_name"]]
    
    return collection.find_one({"Gmail": gmail}, sort=[("Assessment date", -1)])

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # User input section
    st.header("👤 Personal Information")
    name = st.text_input("Full Name", "")
    gmail = st.text_input("Gmail Address", "")

    if st.button("Proceed to Assessment"):
        if not name.strip():
            st.error("❌ Please enter your full name.")
            return

        # Store user session
        st.session_state["name"] = name.strip()
        st.session_state["gmail"] = gmail.strip()

        # Fetch last assessment
        latest_assessment = fetch_latest_assessment(gmail)
        prev_percentage = None

        if latest_assessment:
            prev_percentage = latest_assessment.get("Health Percentage", None)
            prev_category = latest_assessment.get("Results", "Unknown")

            st.success(f"✅ This is your previous result: {prev_percentage}% ({prev_category})")

            with st.expander("📜 View Last Assessment"):
                st.json(latest_assessment)

        st.session_state["assessment_started"] = True

    if "assessment_started" not in st.session_state:
        return

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = st.slider(q["text"], 0, 5)
        
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender")
            return
            
        if client:
            percentage = calculate_health_percentage(responses, QUESTIONS)
            result = get_result_category(percentage)

            try:
                # Save latest assessment (overwrite previous)
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]

                # Remove previous assessment
                collection.delete_many({"Gmail": st.session_state["gmail"]})

                # Insert new assessment
                doc = {
                    "Name": st.session_state["name"],
                    "Gmail": st.session_state["gmail"],
                    **responses,
                    "Gender": gender.strip().title(),
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
                
                # 🔥 Compare new score with previous one
                if prev_percentage is not None:
                    if percentage > prev_percentage:
                        st.success("🎉 You are healthier than before! Keep it up!")
                    elif percentage < prev_percentage:
                        st.warning("⚠️ Your mental health score has decreased. Consider seeking support.")
                    else:
                        st.info("🙂 Your mental health status is stable. Keep maintaining your well-being!")

                with st.expander("View Detailed Breakdown"):
                    st.json(doc)

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
