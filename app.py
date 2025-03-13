import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load questions configuration from questions.json
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

def convert_mongo_docs(docs):
    """Convert MongoDB documents to JSON-serializable format"""
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "Assessment date" in doc and isinstance(doc["Assessment date"], datetime):
            doc["Assessment date"] = doc["Assessment date"].isoformat()
    return docs

def render_question(q):
    """Render a question based on its type"""
    q_type = q.get("type", "positive_scale")
    if q_type == "mood":
        return st.selectbox(q["text"], q["options"])
    elif q_type == "binary_risk":
        return st.radio(q["text"], [("No", "0"), ("Yes", "1")], format_func=lambda x: x[0])[1]
    elif q_type == "number":
        return st.number_input(q["text"], min_value=0, step=1)
    elif "scale" in q_type:
        return st.slider(q["text"], 0, 5)
    return None

def validate_gmail(email):
    """Ensure Gmail is valid"""
    return email.endswith("@gmail.com")

def check_existing_user(name, email):
    """Check if a user with the same name and Gmail already exists"""
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        existing_user = collection.find_one({"Name": name, "Gmail": email})
        return existing_user is not None
    return False

def get_previous_assessment(email):
    """Retrieve the most recent assessment for a user"""
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        prev_assessment = collection.find_one({"Gmail": email}, sort=[("Assessment date", -1)])
        return prev_assessment
    return None

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # User info section (Name & Gmail)
    st.header("\U0001F464 Personal Information")
    name = st.text_input("Full Name", "")
    gmail = st.text_input("Gmail Address", "")

    if st.button("Proceed to Assessment"):
        if not name.strip():
            st.error("❌ Please enter your full name.")
            return
        if not validate_gmail(gmail):
            st.error("❌ Please enter a valid Gmail address (must end with @gmail.com).")
            return
        if check_existing_user(name.strip(), gmail.strip()):
            st.error("❌ A user with this name and Gmail already exists. Please use a different name or email.")
            return

        # Save Name & Gmail
        st.session_state["Name"] = name.strip()
        st.session_state["Gmail"] = gmail.strip()

        # Retrieve last assessment
        prev_assessment = get_previous_assessment(gmail)
        if prev_assessment:
            prev_percentage = prev_assessment.get("Health Percentage", 0.0)
            prev_category = prev_assessment.get("Results", "")

            # Show previous result
            if prev_category != "Unknown":
                st.success(f"✅ This is your previous result: {prev_percentage:.2f}% ({prev_category})")
            else:
                st.success(f"✅ This is your previous result: {prev_percentage:.2f}%")

        # Move to assessment
        st.session_state["assessment_started"] = True

    if "assessment_started" not in st.session_state:
        return  # Stop execution until name & Gmail are provided

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        
        # Gender selection with validation
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender")
            return
            
        if client:
            # Calculate results using custom functions
            percentage = calculate_health_percentage(responses, QUESTIONS)
            result = get_result_category(percentage)

            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]

                # Save new assessment
                doc = {
                    "Name": st.session_state["Name"],
                    "Gmail": st.session_state["Gmail"],
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

                with st.expander("View Detailed Breakdown"):
                    st.json(convert_mongo_docs([doc])[0])

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
