# utils/scheduler.py

def allocate_study_time(student_profile):
    topics = student_profile["topics"]
    total_days = (student_profile["exam_date"] - student_profile["current_date"]).days
    daily_hours = student_profile["daily_study_hours"]
    total_available_hours = total_days * daily_hours

    total_priority = sum(t["priority"] for t in topics if t["priority"] > 0)

    for topic in topics:
        if topic["priority"] == 0 or total_priority == 0:
            topic["allocated_hours"] = 0
        else:
            topic["allocated_hours"] = round((topic["priority"] / total_priority) * total_available_hours, 2)

    return topics
