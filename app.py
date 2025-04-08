import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pymongo import MongoClient
import hashlib
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
        if "Health Percentage" in doc:
            doc["Health Percentage"] = f"{doc['Health Percentage'] * 100:.2f}%"
    return docs

# Password hashing utilities
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, input_password):
    return stored_hash == hash_password(input_password)

# Question rendering
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

# Validators and database fetchers
def validate_gmail(email):
    return email.endswith("@gmail.com")

def get_user_by_email(gmail):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Gmail": gmail})
    return None

def get_previous_assessment(email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Gmail": email}, sort=[("Assessment date", -1)])
    return None

def has_assessment_today(email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return collection.find_one({"Gmail": email, "Assessment date": {"$gte": today}})
    return False

# Main app

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    st.header("\U0001F512 User Login or Registration")
    gmail = st.text_input("Gmail Address", "").strip()
    password = st.text_input("Password", type="password")

    if st.button("Login / Register"):
        if not gmail or not password:
            st.error("❌ Please enter both Gmail and password.")
            return
        if not validate_gmail(gmail):
            st.error("❌ Gmail must end with @gmail.com.")
            return

        user_doc = get_user_by_email(gmail)

        if user_doc:
            if not verify_password(user_doc.get("Password", ""), password):
                st.error("❌ Incorrect password.")
                return
            if has_assessment_today(gmail):
                st.error("❌ You have already submitted an assessment today.")
                return

            st.success("✅ Logged in successfully!")
            st.session_state.update({
                "Name": user_doc["Name"],
                "Gmail": gmail,
                "Age": user_doc.get("Age", 0),
                "Gender": user_doc.get("Gender", "Unknown"),
                "assessment_started": True
            })
        else:
            st.info("New user detected. Please complete registration.")
            name = st.text_input("Full Name (New User)", key="new_name").strip()
            age = st.number_input("Enter your age", min_value=1, max_value=100, step=1, key="new_age")
            gender = st.radio("Gender", ["Male", "Female"], index=None, key="new_gender")

            if name and gender:
                hashed_pw = hash_password(password)
                new_user_doc = {
                    "Name": name,
                    "Gmail": gmail,
                    "Password": hashed_pw,
                    "Age": age,
                    "Gender": gender.strip().title()
                }
                try:
                    db = client[st.secrets["db_name"]]
                    collection = db[st.secrets["collection_name"]]
                    collection.insert_one(new_user_doc)
                    st.success("✅ Registration successful! You may proceed.")
                    st.session_state.update({
                        "Name": name,
                        "Gmail": gmail,
                        "Age": age,
                        "Gender": gender.strip().title(),
                        "assessment_started": True
                    })
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")
            else:
                st.warning("⚠️ Please complete all registration fields.")

    if "assessment_started" not in st.session_state:
        return

    # Assessment Form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted and client:
        percentage = calculate_health_percentage(responses, QUESTIONS)
        result = get_result_category(percentage * 100)

        try:
            db = client[st.secrets["db_name"]]
            collection = db[st.secrets["collection_name"]]
            doc = {
                "Name": st.session_state["Name"],
                "Gmail": st.session_state["Gmail"],
                "Age": st.session_state["Age"],
                **responses,
                "Gender": st.session_state["Gender"],
                "Health Percentage": percentage,
                "Results": result,
                "Assessment date": datetime.now()
            }
            collection.insert_one(doc)
            st.success("✅ Assessment saved successfully!")

            st.subheader("Your Results")
            col1, col2 = st.columns(2)
            col1.metric("Overall Score", f"{percentage * 100:.2f}%")
            col2.metric("Result Category", result)

            with st.expander("View Detailed Breakdown"):
                st.json(convert_mongo_docs([doc])[0])

        except Exception as e:
            st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
