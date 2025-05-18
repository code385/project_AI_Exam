from datetime import datetime
from engine.inference import calculate_priority
from utils.scheduler import allocate_study_time
from engine.working_memory import WorkingMemory

# Initialize working memory
student_memory = WorkingMemory(student_id="12345")

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

# Start a new study session in working memory
student_memory.start_study_session()

# Calculate priority for each topic
for topic in student_profile["topics"]:
    topic["priority"] = calculate_priority(topic)
    
    # Apply any adaptive learning factors from working memory
    # For example, adjust priority based on fatigue and interest
    fatigue = student_memory.adaptive_parameters["fatigue_factor"]
    interest = student_memory.adaptive_parameters["interest_factor"]
    
    # Get mastery level from working memory if available
    mastery = student_memory.estimate_topic_mastery(topic["name"])
    
    # Apply mastery-based adjustment (lower priority if mastery is high)
    mastery_adjustment = 1.0 - (mastery * 0.5)  # reduce priority by up to 50% based on mastery
    
    # Final priority adjustment
    topic["priority"] = topic["priority"] * mastery_adjustment * interest / fatigue
    
    print(f"📘 {topic['name']}: Priority = {topic['priority']:.2f}, Mastery = {mastery:.2f}")

# Allocate study hours based on priorities
planned_topics = allocate_study_time(student_profile)

# Final Output
print("\n📝 Final Study Plan:")
for topic in planned_topics:
    print(f"- {topic['name']}: Priority = {topic['priority']:.2f}, Hours = {topic['allocated_hours']}")
    
    # Record planned study in working memory
    student_memory.record_topic_study(
        topic_name=topic['name'],
        duration_minutes=int(topic['allocated_hours'] * 60)  # convert hours to minutes
    )

# Example of recording performance after a study session
student_memory.record_performance("AI Basics", 65)  # student scored 65 on a quiz
student_memory.record_performance("Search Algorithms", 75)

# End the study session and get summary
session_summary = student_memory.end_study_session()
print("\n✅ Study session completed and recorded in working memory")
print(f"Duration: {session_summary['duration']:.2f} hours")

# Get recommended break based on study duration
break_time = student_memory.get_recommended_break(session_summary['duration'])
print(f"Recommended break: {break_time} minutes before next session")

# Save the memory state
student_memory.save_memory()
print("Memory state saved to file")
