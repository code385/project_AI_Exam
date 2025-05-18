import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid

# Fix module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine.inference import calculate_priority
from utils.scheduler import allocate_study_time
from engine.working_memory import WorkingMemory

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
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    <div class='big-title'>📘 Intelligent Exam Preparation Assistant</div>
    <div class='subtitle'>Plan your study schedule based on performance, difficulty, and topic importance.</div>
""", unsafe_allow_html=True)

# Initialize session state for working memory
if 'student_id' not in st.session_state:
    st.session_state.student_id = str(uuid.uuid4())[:8]  # Generate a unique student ID

if 'memory' not in st.session_state:
    st.session_state.memory = WorkingMemory(student_id=st.session_state.student_id)

# Initialize memory
memory = st.session_state.memory

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 Create Study Plan", "📊 Learning Analytics", "⚙️ Memory Settings"])

# Tab 1: Study Plan Creation
with tab1:
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
                # If we have previous performance data, show it
                mastery = 0
                if name:
                    mastery = memory.estimate_topic_mastery(name)
                    if mastery > 0:
                        st.info(f"Current mastery: {mastery*100:.1f}%")
                
                score = st.slider("Your Score (0–100)", 0, 100, 50, key=f"score_{i}")
                difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key=f"diff_{i}")
                importance = st.selectbox("Importance", ["optional", "important", "core"], key=f"imp_{i}")
                if name:
                    topics.append({
                        "name": name,
                        "score": score,
                        "difficulty": difficulty,
                        "importance": importance,
                        "mastery": mastery
                    })

        # Adaptive parameters
        with st.expander("🧠 Adaptive Learning Parameters"):
            fatigue = st.slider("Fatigue Factor (Higher means more breaks needed)",
                               0.1, 2.0, memory.adaptive_parameters["fatigue_factor"], 0.1)
            interest = st.slider("Interest Factor (Higher means more focus)",
                               0.1, 2.0, memory.adaptive_parameters["interest_factor"], 0.1)
            retention = st.slider("Retention Rate (Higher means better memory)",
                                0.1, 1.0, memory.adaptive_parameters["retention_rate"], 0.1)
            
            # Update memory parameters
            memory.update_adaptive_parameters(
                fatigue_factor=fatigue,
                interest_factor=interest,
                retention_rate=retention
            )

        submitted = st.form_submit_button("🧠 Generate Study Plan")

    # Process and display output
    if submitted and topics:
        # Start a new study session
        memory.start_study_session()
        
        student_profile = {
            "current_date": current_date,
            "exam_date": exam_date,
            "daily_study_hours": daily_hours,
            "topics": topics
        }

        for topic in student_profile["topics"]:
            # Calculate base priority
            topic["priority"] = calculate_priority(topic)
            
            # Apply memory-based adjustments
            mastery = memory.estimate_topic_mastery(topic["name"])
            fatigue = memory.adaptive_parameters["fatigue_factor"]
            interest = memory.adaptive_parameters["interest_factor"]
            
            # Apply mastery-based adjustment (lower priority if mastery is high)
            mastery_adjustment = 1.0 - (mastery * 0.5)  # reduce priority by up to 50% based on mastery
            
            # Final priority adjustment
            topic["priority"] = topic["priority"] * mastery_adjustment * interest / fatigue
            topic["mastery"] = mastery

        plan = allocate_study_time(student_profile)

        # Record planned topics in working memory
        for topic in plan:
            memory.record_topic_study(
                topic_name=topic['name'],
                duration_minutes=int(topic['allocated_hours'] * 60)
            )

        # Save memory state
        memory.save_memory()

        # Display table
        st.success("Study Plan generated successfully! 🎯")
        st.markdown("### ✅ Personalized Study Plan")
        
        df = pd.DataFrame(plan)
        df = df.rename(columns={
            "name": "Topic",
            "priority": "Priority",
            "allocated_hours": "Allocated Hours",
            "mastery": "Mastery %"
        })
        
        # Format mastery as percentage
        if "mastery" in df.columns:
            df["Mastery %"] = df["mastery"].apply(lambda x: f"{x*100:.1f}%" if x is not None else "0.0%")
        
        # Show table
        st.dataframe(df, use_container_width=True)

        # Pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Study Time Distribution")
            fig = px.pie(df, names="Topic", values="Allocated Hours", title="Study Time by Topic")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if "mastery" in df.columns:
                st.markdown("### 🎯 Topic Mastery")
                mastery_df = df[["Topic", "mastery"]].copy()
                mastery_df["mastery"] = mastery_df["mastery"] * 100  # Convert to percentage
                fig = px.bar(mastery_df, x="Topic", y="mastery", 
                            title="Current Topic Mastery (%)",
                            labels={"mastery": "Mastery %", "Topic": "Topic"})
                st.plotly_chart(fig, use_container_width=True)

        # CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Study Plan as CSV",
            data=csv,
            file_name="study_plan.csv",
            mime='text/csv'
        )
        
        # Study session metrics
        st.markdown("### ⏱️ Study Session Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_study_hours = df["Allocated Hours"].sum()
            st.metric("Total Study Hours", f"{total_study_hours:.1f}")
        
        with col2:
            break_mins = memory.get_recommended_break(total_study_hours)
            st.metric("Recommended Break", f"{break_mins} mins")
            
        with col3:
            days_left = (exam_date - current_date).days
            st.metric("Days Until Exam", days_left)

# Tab 2: Learning Analytics from Working Memory
with tab2:
    st.markdown("### 📈 Learning Performance Tracker")
    
    # Get all topics that have performance data
    all_topics = set()
    for topic_name in memory.performance_history.keys():
        all_topics.add(topic_name)
    
    # Also add topics from current session
    for entry in memory.current_session.get("topics_studied", []):
        all_topics.add(entry["topic"])
    
    if not all_topics:
        st.info("No learning data available yet. Create a study plan first.")
    else:
        selected_topic = st.selectbox("Select Topic to Analyze", list(all_topics))
        
        if selected_topic:
            performance_trend = memory.get_performance_trend(selected_topic)
            study_hours = memory.get_study_time_for_topic(selected_topic)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Study Time", f"{study_hours:.1f} hours")
                
                if performance_trend:
                    current_score = performance_trend[-1]["score"] if performance_trend else 0
                    st.metric("Latest Score", f"{current_score}/100")
            
            with col2:
                mastery = memory.estimate_topic_mastery(selected_topic)
                st.metric("Estimated Mastery", f"{mastery*100:.1f}%")
                
                if len(performance_trend) >= 2:
                    improvement = performance_trend[-1]["score"] - performance_trend[0]["score"]
                    st.metric("Overall Improvement", f"{improvement:+.1f} points", 
                             delta=improvement)
            
            if performance_trend:
                # Convert to DataFrame for plotting
                perf_df = pd.DataFrame(performance_trend)
                perf_df["timestamp"] = pd.to_datetime(perf_df["timestamp"])
                
                fig = px.line(perf_df, x="timestamp", y="score", 
                            title=f"Performance Trend: {selected_topic}",
                            labels={"score": "Score", "timestamp": "Date"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No performance data recorded for {selected_topic} yet.")
    
    # Record new performance data
    st.markdown("### 📝 Record New Performance")
    with st.form("record_performance"):
        topic_name = st.selectbox("Topic", list(all_topics) if all_topics else ["No topics available"])
        new_score = st.slider("Score (0-100)", 0, 100, 75)
        submit_score = st.form_submit_button("Record Score")
    
    if submit_score and topic_name != "No topics available":
        memory.record_performance(topic_name, new_score)
        memory.save_memory()
        st.success(f"Score of {new_score} recorded for {topic_name}")
        st.rerun()  # Refresh the page to show new data

# Tab 3: Memory Settings
with tab3:
    st.markdown("### ⚙️ Working Memory Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"Student ID: {st.session_state.student_id}")
        
        if st.button("Reset Working Memory"):
            st.session_state.memory = WorkingMemory(student_id=st.session_state.student_id)
            st.success("Working memory has been reset")
            st.rerun()
    
    with col2:
        # Display memory stats
        session_count = len(memory.session_history)
        performance_entries = sum(len(records) for records in memory.performance_history.values())
        
        st.metric("Total Study Sessions", session_count)
        st.metric("Performance Records", performance_entries)
