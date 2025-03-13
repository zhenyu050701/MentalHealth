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

def get_previous_assessment(name, email):
    """Retrieve the most recent assessment for a user"""
    if client:
        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        prev_assessment = collection.find_one({"Name": name, "Gmail": email}, sort=[("Assessment date", -1)])
        return prev_assessment
    return None

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

        # Retrieve last assessment
        prev_assessment = get_previous_assessment(name, gmail)

        if prev_assessment:
            prev_score = prev_assessment.get("Health Percentage", 0) * 100  # Convert decimal to percentage
            prev_category = prev_assessment.get("Results", "").strip()
            prev_date = prev_assessment.get("Assessment date", "N/A")

            # Format date properly
            if isinstance(prev_date, datetime):
                prev_date = prev_date.strftime("%d/%m/%Y %H:%M")  # Format as DD/MM/YYYY HH:mm

            # Show previous result
            st.subheader("📊 Your Previous Assessment")
            col1, col2, col3 = st.columns(3)
            col1.metric("Previous Score", f"{prev_score:.2f}%")
            col2.metric("Previous Category", prev_category if prev_category else "-")
            col3.metric("Date Taken", prev_date)

            # Store for comparison
            st.session_state["prev_score"] = prev_score
        else:
            st.session_state["prev_score"] = None

        # Save Name & Gmail in session
        st.session_state["Name"] = name.strip()
        st.session_state["Gmail"] = gmail.strip()
        st.session_state["assessment_started"] = True

    if "assessment_started" not in st.session_state:
        return  # Stop execution until user enters correct name & Gmail

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("❌ Please select your gender")
            return
            
        if client:
            # Calculate results using custom functions
            percentage = calculate_health_percentage(responses, QUESTIONS) * 100  # Convert to percentage
            result = get_result_category(percentage)

            try:
                db = client[st.secrets["db_name"]]
                collection = db[st.secrets["collection_name"]]

                # Retrieve the previous assessment before saving new one
                prev_score = st.session_state.get("prev_score")

                # Save new assessment (replace previous one)
                collection.delete_many({"Name": st.session_state["Name"], "Gmail": st.session_state["Gmail"]})
                doc = {
                    "Name": st.session_state["Name"],
                    "Gmail": st.session_state["Gmail"],
                    **responses,
                    "Gender": gender.strip().title(),
                    "Health Percentage": percentage / 100,  # Store as decimal
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

                # Compare with previous result
                if prev_score is not None:
                    if percentage > prev_score:
                        st.success(f"🎉 You are healthier! Your score improved from {prev_score:.2f}% to {percentage:.2f}%.")
                    elif percentage < prev_score:
                        st.warning(f"⚠ Your health has declined. Your score dropped from {prev_score:.2f}% to {percentage:.2f}%.")
                    else:
                        st.info("🔄 No change detected in your mental health score.")

                    # Generate comparison graph
                    df = pd.DataFrame({
                        "Assessment": ["Previous", "Current"],
                        "Score (%)": [prev_score, percentage]
                    })
                    fig = px.bar(df, x="Assessment", y="Score (%)", text="Score (%)", title="Health Score Comparison",
                                 color="Assessment", barmode="group")
                    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    st.plotly_chart(fig)

            except Exception as e:
                st.error(f"❌ Error saving assessment: {str(e)}")

if __name__ == "__main__":
    main()
