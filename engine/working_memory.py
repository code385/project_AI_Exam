# engine/working_memory.py
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class WorkingMemory:
    def __init__(self, student_id: str, memory_file: str = None):
        """
        Initialize working memory for tracking student learning state.
        
        Args:
            student_id: Unique identifier for the student
            memory_file: Optional file path to load/save memory state
        """
        self.student_id = student_id
        self.memory_file = memory_file or f"data/student_{student_id}_memory.json"
        self.current_session = {
            "start_time": datetime.now(),
            "topics_studied": [],
            "performance_metrics": {}
        }
        self.session_history = []
        self.performance_history = {}
        self.adaptive_parameters = {
            "fatigue_factor": 1.0,
            "interest_factor": 1.0,
            "retention_rate": 0.8
        }
        
        # Load existing memory if available
        self._load_memory()
    
    def _load_memory(self) -> None:
        """Load memory from file if it exists."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.session_history = data.get("session_history", [])
                    self.performance_history = data.get("performance_history", {})
                    self.adaptive_parameters = data.get("adaptive_parameters", self.adaptive_parameters)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading memory file: {e}")
    
    def save_memory(self) -> None:
        """Save current memory state to file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        # Prepare data for serialization
        data = {
            "session_history": self.session_history,
            "performance_history": self.performance_history,
            "adaptive_parameters": self.adaptive_parameters
        }
        
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving memory file: {e}")
    
    def start_study_session(self) -> None:
        """Start a new study session."""
        # Save previous session if exists
        if self.current_session and len(self.current_session["topics_studied"]) > 0:
            self.end_study_session()
            
        self.current_session = {
            "start_time": datetime.now(),
            "topics_studied": [],
            "performance_metrics": {}
        }
    
    def end_study_session(self) -> Dict[str, Any]:
        """End current study session and add to history."""
        if not self.current_session:
            return {}
        
        self.current_session["end_time"] = datetime.now()
        self.current_session["duration"] = (
            self.current_session["end_time"] - self.current_session["start_time"]
        ).total_seconds() / 3600  # Convert to hours
        
        session_copy = self.current_session.copy()
        self.session_history.append(session_copy)
        self.save_memory()
        
        return session_copy
    
    def record_topic_study(self, topic_name: str, duration_minutes: int) -> None:
        """
        Record that a topic was studied in the current session.
        
        Args:
            topic_name: Name of the topic studied
            duration_minutes: Time spent studying in minutes
        """
        if not self.current_session:
            self.start_study_session()
            
        self.current_session["topics_studied"].append({
            "topic": topic_name,
            "duration_minutes": duration_minutes,
            "timestamp": datetime.now()
        })
    
    def record_performance(self, topic_name: str, score: float) -> None:
        """
        Record performance for a topic.
        
        Args:
            topic_name: Name of the topic
            score: Score achieved (0-100)
        """
        if topic_name not in self.performance_history:
            self.performance_history[topic_name] = []
            
        self.performance_history[topic_name].append({
            "score": score,
            "timestamp": datetime.now()
        })
        
        # Also record in current session
        if topic_name not in self.current_session["performance_metrics"]:
            self.current_session["performance_metrics"][topic_name] = []
            
        self.current_session["performance_metrics"][topic_name].append({
            "score": score,
            "timestamp": datetime.now()
        })
        
        self.save_memory()
    
    def get_study_time_for_topic(self, topic_name: str) -> float:
        """
        Calculate total time spent studying a topic across all sessions.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            Total time in hours
        """
        total_minutes = 0
        
        # Add time from session history
        for session in self.session_history:
            for topic_entry in session.get("topics_studied", []):
                if topic_entry["topic"] == topic_name:
                    total_minutes += topic_entry["duration_minutes"]
        
        # Add time from current session
        for topic_entry in self.current_session.get("topics_studied", []):
            if topic_entry["topic"] == topic_name:
                total_minutes += topic_entry["duration_minutes"]
                
        return total_minutes / 60  # Convert to hours
    
    def get_performance_trend(self, topic_name: str) -> List[Dict[str, Any]]:
        """
        Get the performance trend for a specific topic.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            List of performance records sorted by timestamp
        """
        if topic_name not in self.performance_history:
            return []
            
        # Sort by timestamp
        return sorted(
            self.performance_history[topic_name],
            key=lambda x: x["timestamp"]
        )
    
    def update_adaptive_parameters(self, fatigue_factor: float = None, 
                                  interest_factor: float = None,
                                  retention_rate: float = None) -> None:
        """
        Update adaptive parameters based on study patterns and performance.
        
        Args:
            fatigue_factor: How quickly student fatigues (0.1-2.0)
            interest_factor: Level of interest in current topics (0.1-2.0)
            retention_rate: Information retention rate (0-1.0)
        """
        if fatigue_factor is not None:
            self.adaptive_parameters["fatigue_factor"] = max(0.1, min(2.0, fatigue_factor))
            
        if interest_factor is not None:
            self.adaptive_parameters["interest_factor"] = max(0.1, min(2.0, interest_factor))
            
        if retention_rate is not None:
            self.adaptive_parameters["retention_rate"] = max(0, min(1.0, retention_rate))
            
        self.save_memory()
    
    def get_recommended_break(self, study_duration: float) -> int:
        """
        Get recommended break time based on study duration and fatigue factor.
        
        Args:
            study_duration: Duration of study session in hours
            
        Returns:
            Recommended break time in minutes
        """
        base_break = 5  # 5-minute base break
        fatigue_factor = self.adaptive_parameters["fatigue_factor"]
        
        # Formula: base_break + (study_duration_in_hours * 10 * fatigue_factor)
        return int(base_break + (study_duration * 10 * fatigue_factor))
    
    def estimate_topic_mastery(self, topic_name: str) -> float:
        """
        Estimate mastery level for a topic based on performance history.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            Estimated mastery level (0-1.0)
        """
        if topic_name not in self.performance_history or not self.performance_history[topic_name]:
            return 0.0
            
        # Get scores sorted by time
        trend = self.get_performance_trend(topic_name)
        scores = [record["score"] for record in trend]
        
        if not scores:
            return 0.0
            
        # Weigh recent scores more heavily
        weighted_sum = 0
        weight_sum = 0
        
        for i, score in enumerate(scores):
            weight = (i + 1)  # More recent scores have higher weights
            weighted_sum += score * weight
            weight_sum += weight
            
        return min(1.0, (weighted_sum / weight_sum) / 100)