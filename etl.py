import json

def load_transform_rules():
    with open("transform_rules.json", "r") as f:
        return json.load(f)
