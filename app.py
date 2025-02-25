import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from calculation import calculate_health_percentage, get_result_category

# Load configuration
with open("questions.json") as f:
    QUESTIONS = json.load(f)

# MongoDB connection
@st.cache_resource
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
        if "timestamp" in doc:
            if isinstance(doc["timestamp"], datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()
    return docs

def render_question(q):
    q_type = q.get("type", "positive_scale")
    if q_type == "mood":
        return st.selectbox(q["text"], q["options"])
    elif q_type == "binary_risk":
        return st.radio(q["text"], [("No", "0"), ("Yes", "1")], format_func=lambda x: x[0])[1]
    elif "scale" in q_type:
        return st.slider(q["text"], 0, 5)
    return None

def show_analytics():
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

        # Convert MongoDB data
        clean_data = convert_mongo_docs(raw_data)
        df = pd.DataFrame(clean_data)

        # Gender Distribution Pie Chart
        st.subheader("👥 Gender Distribution")
        gender_counts = df['gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        
        fig = px.pie(gender_counts,
                     values='Count',
                     names='Gender',
                     color='Gender',
                     color_discrete_map={'Male':'lightcyan',
                                        'Female':'darkblue'},
                     hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

        # Average Scores
        st.subheader("📈 Average Mental Health Scores")
        avg_scores = df.groupby("gender")["health_percentage"].mean().reset_index()
        fig = px.bar(avg_scores, 
                    x="gender", 
                    y="health_percentage",
                    color="gender",
                    text_auto=".2f")
        st.plotly_chart(fig)

        # Score Distribution
        st.subheader("📊 Score Distribution by Gender")
        fig = px.box(df, 
                    x="gender", 
                    y="health_percentage", 
                    color="gender",
                    points="all",
                    hover_data=["stress_level", "anxiety_level", "mood"])
        st.plotly_chart(fig)

        # Result Categories
        st.subheader("🏷️ Result Category Breakdown")
        category_counts = df.groupby(["gender", "result_category"]).size().unstack()
        fig = px.bar(category_counts, 
                    barmode="group",
                    title="Results by Gender")
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your mental health status.")

    # Assessment form
    responses = {}
    with st.form("assessment_form"):
        for q in QUESTIONS:
            responses[q["key"]] = render_question(q)
        
        gender = st.radio("Gender", ["Male", "Female"])
        submitted = st.form_submit_button("Submit Assessment")

    if submitted and client:
        # Calculate results
        percentage = calculate_health_percentage(responses, QUESTIONS)
        result = get_result_category(percentage)

        try:
            # Save to MongoDB
            doc = {
                **responses,
                "gender": gender,
                "health_percentage": percentage,
                "result_category": result,
                "timestamp": datetime.now()
            }
            db = client[st.secrets["db_name"]]
            db[st.secrets["collection_name"]].insert_one(doc)
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

    # Show analytics
    show_analytics()

if __name__ == "__main__":
    main()
