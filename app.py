import streamlit as st
import json
from datetime import datetime
from calculation import calculate_health_percentage, get_result_category
from pymongo import MongoClient

# Load MongoDB credentials from Streamlit secrets
MONGO_URI = st.secrets["mongo_uri"]
DB_NAME = st.secrets["db_name"]
COLLECTION_NAME = st.secrets["collection_name"]

# Connect to MongoDB
@st.cache_resource
def init_mongo_connection():
    try:
        client = MongoClient(MONGO_URI)
        return client
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        return None

client = init_mongo_connection()

# Load questions
with open("questions.json") as f:
    QUESTIONS = json.load(f)

def render_question(question):
    q_type = question.get("type", "positive_scale")
    key = question["key"]
    
    if q_type == "mood":
        return st.selectbox(question["text"], question["options"])
    elif "scale" in q_type:
        return st.slider(question["text"], 0, 5)
    elif q_type == "binary_risk":
        return st.radio(
            question["text"], 
            options=[("No", "0"), ("Yes", "1")],
            format_func=lambda x: x[0]
        )[1]

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your current mental health status.")

    # Initialize session state
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # Collect responses
    responses = {}
    for question in QUESTIONS:
        responses[question["key"]] = render_question(question)

    # Add gender (non-scoring) with only Male/Female
    gender = st.radio("Gender", ["Male", "Female"])

    if st.button("Submit Assessment") and client:
        percentage = calculate_health_percentage(responses, QUESTIONS)
        result = get_result_category(percentage)

        # Create complete document
        document = {
            **responses,
            "gender": gender,
            "health_percentage": percentage,
            "result_category": result,
            "timestamp": datetime.now().isoformat()
        }

        # Insert into MongoDB
        try:
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            collection.insert_one(document)
            st.session_state.submitted = True
            st.success("✅ Assessment saved successfully!")
        except Exception as e:
            st.error(f"❌ Database error: {str(e)}")

        # Show results
        st.subheader(f"Assessment Result: {result}")
        st.metric("Overall Score", f"{percentage}%")
        
        # Detailed breakdown
        with st.expander("Detailed Breakdown"):
            st.json(document)

if __name__ == "__main__":
    main()
