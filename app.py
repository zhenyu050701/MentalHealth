import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

with open("questions.json") as f:
    QUESTIONS = json.load(f)

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
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "Assessment date" in doc and isinstance(doc["Assessment date"], datetime):
            doc["Assessment date"] = doc["Assessment date"].isoformat()
    return docs

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

def validate_gmail(email):
    return email.endswith("@gmail.com")

def get_previous_assessment(name, email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        return collection.find_one({"Name": name, "Gmail": email}, sort=[("Assessment date", -1)])
    return None

def has_assessment_today(name, email):
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return collection.find_one({
            "Name": name,
            "Gmail": email,
            "Assessment date": {"$gte": today}
        })
    return False

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

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
        
        prev_assessment = get_previous_assessment(name, gmail)
        if prev_assessment:
            prev_score = prev_assessment.get("Health Percentage", 0) * 100
            prev_date = prev_assessment.get("Assessment date", "N/A")
            if isinstance(prev_date, datetime):
                prev_date = prev_date.strftime("%d/%m/%Y %H:%M")
            st.subheader("\U0001F4CA Your Previous Assessment")
            col1, col2 = st.columns(2)
            col1.metric("Previous Score", f"{prev_score:.2f}%")
            col2.metric("Date Taken", prev_date)

        if has_assessment_today(name, gmail):
            st.error("❌ You can only submit one assessment per day.")
            return

        st.session_state.update({
            "Name": name,
            "Gmail": gmail,
            "Age": age,
            "Gender": gender.strip().title(),
            "assessment_started": True
        })

    if "assessment_started" not in st.session_state:
        return

    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if client:
            percentage = calculate_health_percentage(responses, QUESTIONS) * 100
            result = get_result_category(percentage)
            
            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]
                doc = {
                    "Name": st.session_state["Name"],
                    "Gmail": st.session_state["Gmail"],
                    "Age": st.session_state["Age"],
                    **responses,
                    "Gender": st.session_state["Gender"],
                    "Health Percentage": percentage / 100, 
                    "Results": result,
                    "Assessment date": datetime.now()
                }
                collection.insert_one(doc)
                st.success("✅ Assessment saved successfully!")
                
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
