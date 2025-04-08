import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load questions from JSON file
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

# Convert MongoDB documents for display
def convert_mongo_docs(docs):
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "Assessment date" in doc and isinstance(doc["Assessment date"], datetime):
            doc["Assessment date"] = doc["Assessment date"].isoformat()
        # Convert stored decimal to percentage for display
        if "Health Percentage" in doc:
            doc["Health Percentage"] = f"{doc['Health Percentage'] * 100:.2f}%"
    return docs

# Function to render questions
def render_question(q):
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

# Validate Gmail address
def validate_gmail(email):
    return email.endswith("@gmail.com")

# Fetch user document by Gmail to validate the name
def get_user_by_email(gmail):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Gmail": gmail})
    return None

# Fetch previous assessment
def get_previous_assessment(name, email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Gmail": email}, sort=[("Assessment date", -1)])
    return None

# Check if user has taken an assessment today
def has_assessment_today(email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return collection.find_one({
            "Gmail": email,
            "Assessment date": {"$gte": today}
        })
    return False

# Check if user is new
def is_new_user(email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Gmail": email}) is None
    return False

# Main application
def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # Personal Information Section
    st.header("\U0001F464 Personal Information")
    name = st.text_input("Full Name", "").strip()
    gmail = st.text_input("Gmail Address", "").strip()
    age = st.number_input("Enter your age", min_value=1, max_value=100, step=1)
    gender = st.radio("Gender", ["Male", "Female"], index=None)

    if st.button("Proceed to Assessment"):
        if not name:
            st.error("❌ Please enter your full name.")
            return
        if not validate_gmail(gmail):
            st.error("❌ Please enter a valid Gmail address (must end with @gmail.com).")
            return
        if not gender:
            st.error("❌ Please select your gender.")
            return

        # Fetch user from the database by Gmail
        user_doc = get_user_by_email(gmail)
        if user_doc:
            # Check if the provided name matches the one stored in the database
            if user_doc["Name"] != name:
                st.error("❌ The name you entered does not match the one on record.")
                return
        else:
            # Register new user in the database
            new_user_doc = {
                "Name": name,
                "Gmail": gmail,
                "Age": age,
                "Gender": gender.strip().title(),
                "Assessment date": None  # New user doesn't have any assessments yet
            }
            if client:
                try:
                    db = client[st.secrets["db_name"]]
                    collection = db[st.secrets["collection_name"]]
                    collection.insert_one(new_user_doc)
                    st.success("✅ Welcome, new user! You have been registered.")
                except Exception as e:
                    st.error(f"❌ Error registering new user: {str(e)}")
                    return

        # Check if the user has already completed the assessment today
        if has_assessment_today(gmail):
            st.error("❌ You can only submit one assessment per day.")
            return

        # Proceed with the assessment as usual
        st.session_state.update({
            "Name": name,
            "Gmail": gmail,
            "Age": age,
            "Gender": gender.strip().title(),
            "assessment_started": True
        })

    if "assessment_started" not in st.session_state:
        return

    # Assessment Form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if client:
            # ✅ FIX: Store percentage as decimal (0.6 instead of 60)
            percentage = calculate_health_percentage(responses, QUESTIONS)  # No multiplication by 100 here
            result = get_result_category(percentage * 100)  # Convert for display

            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]
                doc = {
                    "Name": st.session_state["Name"],
                    "Gmail": st.session_state["Gmail"],
                    "Age": st.session_state["Age"],
                    **responses,
                    "Gender": st.session_state["Gender"],
                    "Health Percentage": percentage,  # ✅ Stored as decimal (e.g., 0.6)
                    "Results": result,
                    "Assessment date": datetime.now()
                }
                collection.insert_one(doc)
                st.success("✅ Assessment saved successfully!")

                # Display Results
                st.subheader("Your Results")
                col1, col2 = st.columns(2)
                col1.metric("Overall Score", f"{percentage * 100:.2f}%")  # ✅ Convert decimal to %
                col2.metric("Result Category", result)

                with st.expander("View Detailed Breakdown"):
                    st.json(convert_mongo_docs([doc])[0])

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
