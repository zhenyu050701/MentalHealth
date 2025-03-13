import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load questions from JSON
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

def validate_gmail(email):
    """Ensure Gmail is valid"""
    return email.endswith("@gmail.com")

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

def get_latest_assessment(db, user_gmail):
    """Retrieve the most recent assessment for a given user"""
    return db[st.secrets["collection_name"]].find_one({"Gmail": user_gmail}, sort=[("Assessment date", -1)])

def show_analytics():
    """Display assessment analytics"""
    st.header("📊 Assessment Analytics")
    try:
        if not client:
            return

        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        raw_data = list(collection.find())
        
        if not raw_data:
            st.warning("No data available yet. Complete an assessment first!")
            return

        # Convert and clean data
        clean_data = convert_mongo_docs(raw_data)
        df = pd.DataFrame(clean_data)

        st.subheader("👥 Gender Distribution")
        gender_counts = df['Gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        fig = px.pie(gender_counts,
                     values='Count',
                     names='Gender',
                     color='Gender',
                     hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # User info section (Name & Gmail)
    st.header("👤 Personal Information")
    name = st.text_input("Full Name", "")
    gmail = st.text_input("Gmail Address", "")

    if st.button("Proceed to Assessment"):
        if not name.strip():
            st.error("❌ Please enter your full name.")
            return
        if not validate_gmail(gmail):
            st.error("❌ Please enter a valid Gmail address (must end with @gmail.com).")
            return

        # Save user info
        st.session_state["name"] = name.strip()
        st.session_state["gmail"] = gmail.strip()
        st.session_state["assessment_started"] = True

    if "assessment_started" not in st.session_state:
        return  # Stop execution until name & Gmail are provided

    # Connect to database
    db = client[st.secrets["db_name"]]
    user_gmail = st.session_state["gmail"]

    # Retrieve the most recent assessment
    latest_assessment = get_latest_assessment(db, user_gmail)
    if latest_assessment:
        prev_percentage = latest_assessment.get("Health Percentage", None)
        prev_category = latest_assessment.get("Results", "Unknown")

        if prev_percentage is not None:
            prev_percentage *= 100  # Convert decimal to percentage format

        st.success(f"✅ This is your previous result: {prev_percentage:.2f}% ({prev_category})")

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        
        # Gender selection
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender")
            return
            
        # Calculate results
        percentage = calculate_health_percentage(responses, QUESTIONS)
        result = get_result_category(percentage)

        try:
            # Save the latest assessment (Overwrite previous one)
            doc = {
                "Name": st.session_state["name"],
                "Gmail": user_gmail,
                **responses,
                "Gender": gender.strip().title(),
                "Health Percentage": percentage,
                "Results": result,
                "Assessment date": datetime.now()
            }

            db[st.secrets["collection_name"]].delete_many({"Gmail": user_gmail})  # Remove old records
            db[st.secrets["collection_name"]].insert_one(doc)  # Save only the latest one

            st.success("✅ Assessment saved successfully!")

            # Show results
            st.subheader("Your Results")
            col1, col2 = st.columns(2)
            col1.metric("Overall Score", f"{percentage * 100:.2f}%")
            col2.metric("Result Category", result)
            
            # Health improvement message
            if latest_assessment and "Health Percentage" in latest_assessment:
                prev_percentage = latest_assessment["Health Percentage"] * 100
                if percentage * 100 > prev_percentage:
                    st.success(f"🎉 You are healthier than before! Previous: {prev_percentage:.2f}%, Now: {percentage * 100:.2f}%")
                elif percentage * 100 < prev_percentage:
                    st.warning(f"⚠ Your mental health has declined. Previous: {prev_percentage:.2f}%, Now: {percentage * 100:.2f}%")
                else:
                    st.info("ℹ Your mental health status remains the same.")

            with st.expander("View Detailed Breakdown"):
                st.json(convert_mongo_docs([doc])[0])

        except Exception as e:
            st.error(f"❌ Error saving assessment: {str(e)}")

    # Show analytics
    show_analytics()

if __name__ == "__main__":
    main()
