# app.py
from questions import ask_questions
from calculation import calculate_health_percentage, determine_result
from database import save_to_database
import datetime

def main():
    user_data = ask_questions()
    user_data["Assessment date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data["Health Percentage"] = calculate_health_percentage(user_data)
    user_data["Results"] = determine_result(user_data["Health Percentage"])
    save_to_database(user_data)
    print("\nAssessment Complete! Your result:")
    print(f"Health Percentage: {user_data['Health Percentage']} - {user_data['Results']}")

if __name__ == "__main__":
    main()
