import json

# Load transform rules
with open("transform_rules.json", "r") as f:
    transform_rules = json.load(f)

def calculate_health_percentage(responses):
    total_score = 0
    max_score = 0
    
    for key, value in responses.items():
        if key in transform_rules:
            total_score += transform_rules[key].get(str(value), value)
        else:
            total_score += value
        max_score += 5
    
    return round((total_score / max_score) * 100, 2)

def get_result_category(health_percentage):
    if health_percentage <= 20:
        return "Poor ❌"
    elif health_percentage <= 40:
        return "Bad ❗"
    elif health_percentage <= 60:
        return "Average ⚠️"
    elif health_percentage <= 80:
        return "Good ✅"
    else:
        return "Excellent ✨"
