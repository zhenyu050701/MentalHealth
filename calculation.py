import json

with open("transform_rules.json", "r") as f:
    TRANSFORM_RULES = json.load(f)

def calculate_health_percentage(responses, questions):
    total_score = 0
    max_score = 0
    
    for question in questions:
        key = question["key"]
        q_type = question.get("type", "positive_scale")
        value = str(responses.get(key, 0))
        
        if q_type == "mood":
            score = TRANSFORM_RULES["mood"].get(value, 50)
            total_score += score
            max_score += 100
        else:
            scale_type = "negative_scale" if "negative" in q_type else "positive_scale"
            score = TRANSFORM_RULES[scale_type].get(value, 0)
            total_score += score
            max_score += 100

    return round((total_score / max_score) * 100, 2) if max_score > 0 else 0

def get_result_category(percentage):
    if percentage >= 85: return "Excellent ✨"
    if percentage >= 70: return "Good ✅"
    if percentage >= 50: return "Fair ⚠️"
    if percentage >= 30: return "Needs Help ❗"
    return "Critical Risk 🔴"
