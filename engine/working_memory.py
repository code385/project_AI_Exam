# engine/working_memory.py
import json,os
from datetime import datetime
from typing import Dict,List,Any

class WorkingMemory:
    def __init__(self,student_id:str,memory_file:str=None):
        self.student_id=student_id
        self.memory_file=memory_file or f"data/student_{student_id}_memory.json"
        self.current_session={"start_time":datetime.now(),"topics_studied":[],"performance_metrics":{}}
        self.session_history=[]
        self.performance_history={}
        self.adaptive_parameters={"fatigue_factor":1.0,"interest_factor":1.0,"retention_rate":0.8}
        self._load_memory()
    
    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file,'r') as f:
                    data=json.load(f)
                    self.session_history=data.get("session_history",[])
                    self.performance_history=data.get("performance_history",{})
                    self.adaptive_parameters=data.get("adaptive_parameters",self.adaptive_parameters)
            except:pass
    
    def save_memory(self):
        os.makedirs(os.path.dirname(self.memory_file),exist_ok=True)
        try:
            with open(self.memory_file,'w') as f:
                json.dump({"session_history":self.session_history,"performance_history":self.performance_history,"adaptive_parameters":self.adaptive_parameters},f,default=str)
        except:pass
    
    def start_study_session(self):
        if self.current_session and len(self.current_session["topics_studied"])>0:self.end_study_session()
        self.current_session={"start_time":datetime.now(),"topics_studied":[],"performance_metrics":{}}
    
    def end_study_session(self):
        if not self.current_session:return {}
        self.current_session["end_time"]=datetime.now()
        self.current_session["duration"]=(self.current_session["end_time"]-self.current_session["start_time"]).total_seconds()/3600
        self.session_history.append(self.current_session.copy())
        self.save_memory()
        return self.current_session.copy()
    
    def record_topic_study(self,topic_name:str,duration_minutes:int):
        if not self.current_session:self.start_study_session()
        self.current_session["topics_studied"].append({"topic":topic_name,"duration_minutes":duration_minutes,"timestamp":datetime.now()})
    
    def record_performance(self,topic_name:str,score:float):
        data={"score":score,"timestamp":datetime.now()}
        if topic_name not in self.performance_history:self.performance_history[topic_name]=[]
        self.performance_history[topic_name].append(data)
        if topic_name not in self.current_session["performance_metrics"]:self.current_session["performance_metrics"][topic_name]=[]
        self.current_session["performance_metrics"][topic_name].append(data)
        self.save_memory()
    
    def get_study_time_for_topic(self,topic_name:str):
        mins=0
        for s in self.session_history:mins+=sum(e["duration_minutes"] for e in s.get("topics_studied",[]) if e["topic"]==topic_name)
        mins+=sum(e["duration_minutes"] for e in self.current_session.get("topics_studied",[]) if e["topic"]==topic_name)
        return mins/60
    
    def get_performance_trend(self,topic_name:str):
        if topic_name not in self.performance_history:return []
        return sorted(self.performance_history[topic_name],key=lambda x:x["timestamp"])
    
    def update_adaptive_parameters(self,fatigue_factor=None,interest_factor=None,retention_rate=None):
        if fatigue_factor:self.adaptive_parameters["fatigue_factor"]=max(0.1,min(2.0,fatigue_factor))
        if interest_factor:self.adaptive_parameters["interest_factor"]=max(0.1,min(2.0,interest_factor))
        if retention_rate:self.adaptive_parameters["retention_rate"]=max(0,min(1.0,retention_rate))
        self.save_memory()
    
    def get_recommended_break(self,study_duration:float):
        return int(5+(study_duration*10*self.adaptive_parameters["fatigue_factor"]))
    
    def estimate_topic_mastery(self,topic_name:str):
        if topic_name not in self.performance_history or not self.performance_history[topic_name]:return 0.0
        scores=[r["score"] for r in self.get_performance_trend(topic_name)]
        if not scores:return 0.0
        w_sum,weights=0,0
        for i,s in enumerate(scores):
            w=i+1
            w_sum+=s*w
            weights+=w
        return min(1.0,(w_sum/weights)/100)
