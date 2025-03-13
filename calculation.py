import json

# Load transform rules
with open("transform_rules.json", "r") as f:
    TRANSFORM_RULES = json.load(f)

def calculate_health_percentage(responses, questions):
    total_score = 0
    max_score = 0
    
    for question in questions:
        key = question["key"]
        q_type = question.get("type", "positive_scale")
        value = str(responses.get(key, "0"))  # Ensure string conversion
        
        if q_type == "mood":
            score = TRANSFORM_RULES["mood"].get(value, 50)
        elif q_type == "binary_risk":
            score = TRANSFORM_RULES["binary_risk"].get(value, 0)
        else:
            scale_type = "negative_scale" if "negative" in q_type else "positive_scale"
            score = TRANSFORM_RULES[scale_type].get(value, 0)
        
        total_score += score
        max_score += 100

    return round(total_score / max_score, 4) if max_score > 0 else 0  # Store in decimal (e.g., 0.5467)

def get_result_category(percentage):
    if percentage >= 0.85: return "Excellent ✨"
    if percentage >= 0.70: return "Good ✅"
    if percentage >= 0.50: return "Fair ⚠️"
    if percentage >= 0.30: return "Needs Help ❗"
    return "Critical Risk 🔴"

def format_percentage(value):
    """Convert stored decimal (e.g., 0.5467) to display format (54.67%)"""
    return f"{value * 100:.2f}%" 

# Example usage
if __name__ == "__main__":
    sample_responses = {"q1": "3", "q2": "yes", "q3": "5"}
    sample_questions = [
        {"key": "q1", "type": "positive_scale"},
        {"key": "q2", "type": "binary_risk"},
        {"key": "q3", "type": "mood"}
    ]
    
    # Calculate and store as decimal
    health_percentage = calculate_health_percentage(sample_responses, sample_questions)
    print("Stored in DB:", health_percentage)  # Example: 0.5467
    
    # Display formatted as percentage
    print("Displayed:", format_percentage(health_percentage))  # Example: 54.67%
    
    # Get result category
    print("Category:", get_result_category(health_percentage))
