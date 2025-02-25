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
    st.title("Mental Health Risk Assessment")
    
    questions = [
        "Do you feel hopeless?",
        "Do you have trouble sleeping?",
        "Do you experience frequent mood swings?",
        "Do you feel overwhelmed often?",
        "Have you lost interest in activities you once enjoyed?",
        "Do you feel lonely?",
        "Do you have difficulty concentrating?",
        "Do you feel tired or lack energy often?",
        "Do you experience physical symptoms like headaches or stomach aches due to stress?",
        "Do you have thoughts of self-harm?",
        "Have you experienced a recent traumatic event?"
    ]
    
    responses = []
    
    for q in questions:
        if q in ["Do you have thoughts of self-harm?", "Have you experienced a recent traumatic event?"]:
            response = st.radio(q, [0, 1], index=0)
        else:
            response = st.slider(q, 0, 5, 0)
        responses.append(response)
    
    if st.button("Submit"):
        total_score = calculate_score(responses)
        result = get_result_category(total_score)
        health_percentage = max(0, 100 - (total_score * 2))
        
        st.session_state.submitted = True
        st.session_state.health_percentage = health_percentage
        st.session_state.result = result
    
    if "submitted" in st.session_state and st.session_state.submitted:
        st.write(f"### Your Health Score: {st.session_state.health_percentage}%")
        st.write(f"### Risk Level: {'High Risk' if st.session_state.result == 1 else 'Low Risk'}")

if __name__ == "__main__":
    main()
