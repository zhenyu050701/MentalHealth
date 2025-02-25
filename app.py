import streamlit as st
import json
from datetime import datetime
from calculation import calculate_health_percentage, get_result_category

# Load questions and config
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
        return st.radio(question["text"], options=[("No", 0), ("Yes", 1)], format_func=lambda x: x[0])[1]

def main():
    st.title("Mental Health Assessment")
    st.write("Complete this assessment to evaluate your current mental health status.")

    # Collect responses
    responses = {"timestamp": datetime.now().isoformat()}
    for question in QUESTIONS:
        responses[question["key"]] = render_question(question)

    # Add gender separately
    responses["gender"] = st.radio("Gender", ["Male", "Female", "Other/Prefer not to say"])

    if st.button("Submit Assessment"):
        percentage = calculate_health_percentage(responses, QUESTIONS)
        result = get_result_category(percentage)
        
        # Show results
        st.subheader(f"Assessment Result: {result}")
        st.metric("Overall Score", f"{percentage}%")
        
        # Show detailed breakdown
        with st.expander("Detailed Breakdown"):
            for q in QUESTIONS:
                st.write(f"**{q['text']}:** {responses[q['key']]}")

if __name__ == "__main__":
    main()
