import streamlit as st
import pandas as pd
import pymongo
from datetime import datetime

# MongoDB Connection
client = pymongo.MongoClient(st.secrets["mongo_uri"])

# Function to clean gender data
def clean_gender_data(df):
    df["Gender"] = df["Gender"].str.strip().str.title()
    return df

# Function to convert MongoDB documents into a DataFrame-compatible format
def convert_mongo_docs(raw_data):
    return [{key: doc[key] for key in doc if key != "_id"} for doc in raw_data]

# Function to calculate health percentage
def calculate_health_percentage(responses):
    yes_answers = sum(1 for ans in responses.values() if ans.lower() == "yes")
    total_questions = len(responses)
    return (yes_answers / total_questions) * 100 if total_questions else 0

# Function to get result category
def get_result_category(percentage):
    if percentage >= 80:
        return "Excellent Health"
    elif percentage >= 50:
        return "Average Health"
    else:
        return "Needs Improvement"

# Function to display analytics (Only if the user has submitted an assessment)
def show_analytics():
    if "gmail" not in st.session_state:
        return  # Stop if Gmail is not set

    st.header("📊 Assessment Analytics")
    try:
        if not client:
            return

        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]

        # Retrieve only the data submitted by the logged-in user
        raw_data = list(collection.find({"Gmail": st.session_state["gmail"]}))

        if not raw_data:
            st.warning("📢 Complete and submit at least one assessment to view analytics!")
            return  # Stop here if no assessment data exists

        # Convert and clean data
        clean_data = convert_mongo_docs(raw_data)
        df = pd.DataFrame(clean_data)
        df = clean_gender_data(df)

        # (Insert Graph Code Here) 📊📈
        st.write(df)  # Placeholder for graphs

    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

# Streamlit UI
def main():
    st.title("🩺 Health Assessment App")

    # Input Fields
    st.session_state["name"] = st.text_input("Enter your Name", key="name_input")
    st.session_state["gmail"] = st.text_input("Enter your Gmail", key="gmail_input")
    gender = st.selectbox("Select your Gender", ["", "Male", "Female", "Other"])

    responses = {}
    for i in range(1, 6):  # Change the range based on the number of questions
        responses[f"Q{i}"] = st.radio(f"Question {i}", ["Yes", "No"], key=f"q{i}")

    # Submit Button
    submitted = st.button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("⚠️ Please select your gender before submitting.")
        else:
            db = client[st.secrets["db_name"]]
            collection = db[st.secrets["collection_name"]]

            assessment_data = {
                "Name": st.session_state["name"],
                "Gmail": st.session_state["gmail"],
                "Gender": gender,
                "Responses": responses,
                "HealthScore": calculate_health_percentage(responses),
                "Category": get_result_category(calculate_health_percentage(responses)),
                "Timestamp": datetime.utcnow(),
            }

            collection.insert_one(assessment_data)
            st.success("✅ Assessment submitted successfully!")

    # Show analytics only if an assessment has been submitted
    if submitted:
        show_analytics()

if __name__ == "__main__":
    main()
