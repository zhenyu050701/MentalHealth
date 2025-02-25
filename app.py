import streamlit as st
import pandas as pd

def calculate_score(responses):
    """Calculate total score based on responses"""
    return sum(responses)

def get_result_category(score):
    """Categorizes the mental health score into binary risk levels"""
    if score < 20:
        return 1  # High Risk
    else:
        return 0  # Low Risk

def main():
    st.title("Mental Wellness Check-In")
    
    gender = st.radio("Select your gender:", ["Male", "Female"])
    
    questions = [
        "Do you often feel a sense of hopelessness or despair?",
        "Are you struggling with sleep issues, such as insomnia or oversleeping?",
        "Do your moods change unpredictably or frequently?",
        "Do you often feel overwhelmed by daily tasks and responsibilities?",
        "Have you lost interest in hobbies or activities that used to bring you joy?",
        "Do you often feel isolated or disconnected from others?",
        "Do you struggle with maintaining focus or concentration?",
        "Do you frequently feel exhausted or drained, even after resting?",
        "Do you experience physical discomfort, such as headaches or stomach aches, due to stress?",
        "Have you engaged in self-harm? (0 = No, 1 = Yes)",
        "Have you recently experienced a traumatic event? (0 = No, 1 = Yes)"
    ]
    
    responses = []
    
    for q in questions:
        if q in ["Have you engaged in self-harm? (0 = No, 1 = Yes)", "Have you recently experienced a traumatic event? (0 = No, 1 = Yes)"]:
            response = st.radio(q, [0, 1], index=0)
        else:
            response = st.slider(q, 0, 5, 0)
        responses.append(response)
    
    if st.button("Submit Assessment"):
        total_score = calculate_score(responses)
        result = get_result_category(total_score)
        health_percentage = max(0, 100 - (total_score * 2))
        
        st.session_state.submitted = True
        st.session_state.health_percentage = health_percentage
        st.session_state.result = result
    
    if "submitted" in st.session_state and st.session_state.submitted:
        st.write(f"### Your Mental Wellness Score: {st.session_state.health_percentage}%")
        st.write(f"### Risk Level: {'High Risk' if st.session_state.result == 1 else 'Low Risk'}")

if __name__ == "__main__":
    main()
