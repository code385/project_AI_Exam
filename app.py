import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

# Fix module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine.inference import calculate_priority
from utils.scheduler import allocate_study_time

# Streamlit settings
st.set_page_config(page_title="Exam Prep Assistant", layout="wide")

# Custom styling
st.markdown("""
    <style>
    .big-title {
        font-size:40px !important;
        color: #4CAF50;
        font-weight: bold;
    }
    .subtitle {
        font-size:20px !important;
        color: #666;
    }
    </style>
    <div class='big-title'>📘 Intelligent Exam Preparation Assistant</div>
    <div class='subtitle'>Plan your study schedule based on performance, difficulty, and topic importance.</div>
""", unsafe_allow_html=True)

# Student profile form
with st.form("exam_form"):
    st.markdown("### 🧑‍🎓 Student Details")

    exam_date = st.date_input("📅 Exam Date", value=datetime(2025, 6, 10))
    current_date = st.date_input("🕒 Today's Date", value=datetime.today())
    daily_hours = st.slider("⏱️ Daily Study Hours", 1, 10, 4)
    topic_count = st.number_input("📚 Number of Topics", min_value=1, max_value=20, value=5, step=1)

    st.markdown("### 📘 Enter Topic Details")

    topics = []
    for i in range(topic_count):
        with st.expander(f"Topic {i+1}"):
            name = st.text_input(f"Topic Name", key=f"name_{i}")
            score = st.slider("Your Score (0–100)", 0, 100, 50, key=f"score_{i}")
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key=f"diff_{i}")
            importance = st.selectbox("Importance", ["optional", "important", "core"], key=f"imp_{i}")
            if name:
                topics.append({
                    "name": name,
                    "score": score,
                    "difficulty": difficulty,
                    "importance": importance
                })

    submitted = st.form_submit_button("🧠 Generate Study Plan")

# Process and display output
if submitted and topics:
    student_profile = {
        "current_date": current_date,
        "exam_date": exam_date,
        "daily_study_hours": daily_hours,
        "topics": topics
    }

    for topic in student_profile["topics"]:
        topic["priority"] = calculate_priority(topic)

    plan = allocate_study_time(student_profile)

    # Display table
    st.success("Study Plan generated successfully! 🎯")
    st.markdown("### ✅ Personalized Study Plan")
    df = pd.DataFrame(plan)
    df = df.rename(columns={
        "name": "Topic",
        "priority": "Priority",
        "allocated_hours": "Allocated Hours"
    })
    st.dataframe(df, use_container_width=True)

    # Pie chart
    st.markdown("### 📊 Study Time Distribution")
    fig = px.pie(df, names="Topic", values="Allocated Hours", title="Study Time by Topic")
    st.plotly_chart(fig)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Study Plan as CSV",
        data=csv,
        file_name="study_plan.csv",
        mime='text/csv'
    )
