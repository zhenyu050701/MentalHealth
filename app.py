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

# Initialize MongoDB connection using secrets (adjust your secrets accordingly)
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
        if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
    return docs

def clean_gender_data(df):
    """Standardize and clean gender column"""
    df['Gender'] = df['Gender'].astype(str).str.strip().str.title()
    valid_genders = ['Male', 'Female']
    df = df[df['Gender'].isin(valid_genders)].copy()
    df.reset_index(drop=True, inplace=True)
    return df

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

        # Convert and clean data
        clean_data = convert_mongo_docs(raw_data)
        df = pd.DataFrame(clean_data)
        df = clean_gender_data(df)

        st.subheader("👥 Gender Distribution")
        gender_counts = df['Gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        all_genders = pd.DataFrame({'Gender': ['Male', 'Female'], 'Count': [0, 0]})
        gender_counts = pd.concat([gender_counts, all_genders])
        gender_counts = gender_counts.groupby('Gender', as_index=False)['Count'].sum()
        fig = px.pie(gender_counts,
                     values='Count',
                     names='Gender',
                     color='Gender',
                     color_discrete_map={'Male':'#1f77b4', 'Female':'#ff7f0e'},
                     hole=0.3)
        fig.update_traces(texttemplate='%{label}<br>%{value} (%{percent})',
                          hoverinfo='label+percent+value')
        st.plotly_chart(fig, use_container_width=True)

        # Additional analytics can be added here

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
        
        # Gender selection with validation
        gender = st.radio("Gender", ["Male", "Female"], index=None)
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        if not gender:
            st.error("Please select your gender")
            return
            
        if client:
            # Calculate results using custom functions
            percentage = calculate_health_percentage(responses, QUESTIONS)
            result = get_result_category(percentage)

            try:
                # Save to MongoDB
                doc = {
                    **responses,
                    "Gender": gender.strip().title(),
                    "Health Percentage": percentage,
                    "Results ": result,
                    "Assessment date": datetime.now()
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

    # Show analytics section
    show_analytics()

if __name__ == "__main__":
    main()
