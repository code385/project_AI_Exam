from datetime import datetime
from engine.inference import calculate_priority
from utils.scheduler import allocate_study_time

# Sample topic input
topics = [
    {
        "name": "AI Basics",
        "difficulty": "hard",     # easy, medium, hard
        "score": 45,              # 0–100
        "importance": "core"      # optional, important, core
    },
    {
        "name": "Search Algorithms",
        "difficulty": "medium",
        "score": 70,
        "importance": "important"
    },
    {
        "name": "Fuzzy Logic",
        "difficulty": "easy",
        "score": 90,
        "importance": "optional"
    }
]

# Student profile (input)
student_profile = {
    "current_date": datetime.strptime("2025-05-02", "%Y-%m-%d"),
    "exam_date": datetime.strptime("2025-06-10", "%Y-%m-%d"),
    "daily_study_hours": 4,
    "topics": topics
}

# Print time until exam
days_left = (student_profile["exam_date"] - student_profile["current_date"]).days
print(f"🕒 Days left until exam: {days_left}")

# Calculate priority for each topic
for topic in student_profile["topics"]:
    topic["priority"] = calculate_priority(topic)
    print(f"📘 {topic['name']}: Priority = {topic['priority']}")

# Allocate study hours based on priorities
planned_topics = allocate_study_time(student_profile)

# Final Output
print("\n📝 Final Study Plan:")
for topic in planned_topics:
    print(f"- {topic['name']}: Priority = {topic['priority']}, Hours = {topic['allocated_hours']}")
