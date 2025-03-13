import json

# Load transformation rules from JSON file
with open("transform_rules.json", "r") as file:
    TRANSFORM_RULES = json.load(file)

def calculate_health_percentage(responses, questions):
    total_score = 0
    max_score = 0

    for q in questions:
        key = q["key"]
        q_type = q["type"]
        response = str(responses.get(key, "0"))  # Default to "0" if not found

        if q_type in TRANSFORM_RULES:
            # Convert binary risk "yes" or "no" to "1" or "0"
            if q_type == "binary_risk":
                response = response.lower()
                if response == "yes":
                    response = "1"
                elif response == "no":
                    response = "0"

            score = TRANSFORM_RULES[q_type].get(response, 0)
            total_score += score
            max_score += max(TRANSFORM_RULES[q_type].values())

    if max_score == 0:
        return 0.0  # Avoid division by zero

    percentage = total_score / max_score
    return percentage

def get_result_category(percentage):

    
    if percentage >= 85:
        return "Excellent ✨"
    elif percentage >= 70:
        return "Good ✅"
    elif percentage >= 50:
        return "Fair ⚠️"
    elif percentage >= 30:
        return "Needs Help ❗"
    else:
        return "Critical Risk 🔴"

# Example usage
if __name__ == "__main__":
    sample_responses = {"q1": "3", "q2": "yes", "q3": "5"}
    sample_questions = [
        {"key": "q1", "type": "positive_scale"},
        {"key": "q2", "type": "binary_risk"},
        {"key": "q3", "type": "mood"}
    ]

    health_percentage = calculate_health_percentage(sample_responses, sample_questions)
    result = get_result_category(health_percentage)

    print(f"Health Percentage: {health_percentage * 100:.2f}%")
    print(f"Result: {result}")
