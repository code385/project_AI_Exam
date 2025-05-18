import streamlit as st,sys,os,uuid,pandas as pd,plotly.express as px
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from engine.inference import calculate_priority
from utils.scheduler import allocate_study_time
from engine.working_memory import WorkingMemory

st.set_page_config(page_title="Exam Prep",layout="wide")
st.markdown("<div class='big-title'>📘 Intelligent Exam Preparation</div><div class='subtitle'>Study planning based on performance</div><style>.big-title{font-size:36px!important;color:#4CAF50;font-weight:bold}.subtitle{font-size:18px!important;color:#666}</style>",unsafe_allow_html=True)

if 'student_id' not in st.session_state: st.session_state.student_id=str(uuid.uuid4())[:8]
if 'memory' not in st.session_state: st.session_state.memory=WorkingMemory(student_id=st.session_state.student_id)
memory=st.session_state.memory

tab1,tab2,tab3=st.tabs(["📝 Plan","📊 Analytics","🧠 Working Memory"])

with tab1:
    with st.form("exam_form"):
        st.markdown("### 🧑‍🎓 Student Details")
        c1,c2=st.columns(2)
        with c1:
            exam_date=st.date_input("📅 Exam Date",value=datetime(2025,6,10))
            current_date=st.date_input("🕒 Today",value=datetime.today())
        with c2:
            daily_hours=st.slider("⏱️ Hours/Day",1,10,4)
            topic_count=st.number_input("📚 Topics",1,20,5)

        st.markdown("### 📘 Topics")
        topics=[]
        for i in range(topic_count):
            with st.expander(f"Topic {i+1}"):
                name=st.text_input("Name",key=f"name_{i}")
                mastery=memory.estimate_topic_mastery(name) if name else 0
                if mastery>0: st.info(f"Mastery: {mastery*100:.1f}%")
                score=st.slider("Score",0,100,50,key=f"score_{i}")
                diff=st.selectbox("Difficulty",["easy","medium","hard"],key=f"diff_{i}")
                imp=st.selectbox("Importance",["optional","important","core"],key=f"imp_{i}")
                if name: topics.append({"name":name,"score":score,"difficulty":diff,"importance":imp,"mastery":mastery})

        with st.expander("🧠 Adaptive"):
            f=st.slider("Fatigue",0.1,2.0,memory.adaptive_parameters["fatigue_factor"],0.1)
            i=st.slider("Interest",0.1,2.0,memory.adaptive_parameters["interest_factor"],0.1)
            r=st.slider("Retention",0.1,1.0,memory.adaptive_parameters["retention_rate"],0.1)
            memory.update_adaptive_parameters(fatigue_factor=f,interest_factor=i,retention_rate=r)

        submitted=st.form_submit_button("Generate Plan")

    if submitted and topics:
        memory.start_study_session()
        profile={"current_date":current_date,"exam_date":exam_date,"daily_study_hours":daily_hours,"topics":topics}
        
        for topic in profile["topics"]:
            base=calculate_priority(topic)
            m=topic["mastery"]
            f,i=memory.adaptive_parameters["fatigue_factor"],memory.adaptive_parameters["interest_factor"]
            topic["priority"]=base*(1.0-m*0.5)*i/f

        plan=allocate_study_time(profile)
        for topic in plan:
            memory.record_topic_study(topic["name"],int(topic["allocated_hours"]*60))
        memory.save_memory()

        st.success("Plan generated!")
        
        df=pd.DataFrame(plan)
        df=df.rename(columns={"name":"Topic","priority":"Priority","allocated_hours":"Hours","mastery":"Mastery"})
        if "mastery" in df.columns:
            df["Mastery"]=df["mastery"].apply(lambda x:f"{x*100:.1f}%" if x is not None else "0%")
        
        st.markdown("### ✅ Plan")
        st.dataframe(df,use_container_width=True)
        
        c1,c2=st.columns(2)
        with c1: st.plotly_chart(px.pie(df,names="Topic",values="Hours",title="Time"),use_container_width=True)
        with c2:
            if "mastery" in df.columns:
                mdf=df[["Topic","mastery"]].copy()
                mdf["mastery"]*=100
                st.plotly_chart(px.bar(mdf,x="Topic",y="mastery",title="Mastery %",labels={"mastery":"%"}),use_container_width=True)

        st.download_button("📥 Download CSV",df.to_csv(index=False).encode('utf-8'),"plan.csv","text/csv")
        
        c1,c2,c3=st.columns(3)
        total=df["Hours"].sum()
        with c1: st.metric("Hours",f"{total:.1f}")
        with c2: st.metric("Break",f"{memory.get_recommended_break(total)}min")
        with c3: st.metric("Days Left",(exam_date-current_date).days)

with tab2:
    st.markdown("### 📈 Performance")
    
    topics=set()
    topics.update(memory.performance_history.keys())
    topics.update(entry["topic"] for entry in memory.current_session.get("topics_studied",[]))
    
    if not topics:
        st.info("No data yet. Create a plan first.")
    else:
        selected=st.selectbox("Topic",list(topics))
        
        if selected:
            perf=memory.get_performance_trend(selected)
            hours=memory.get_study_time_for_topic(selected)
            
            c1,c2=st.columns(2)
            with c1:
                st.metric("Study Time",f"{hours:.1f}hrs")
                if perf: st.metric("Latest Score",f"{perf[-1]['score']}/100")
            with c2:
                st.metric("Mastery",f"{memory.estimate_topic_mastery(selected)*100:.1f}%")
                if len(perf)>=2:
                    imp=perf[-1]["score"]-perf[0]["score"]
                    st.metric("Improvement",f"{imp:+.1f}",delta=imp)
            
            if perf:
                df=pd.DataFrame(perf)
                df["timestamp"]=pd.to_datetime(df["timestamp"])
                st.plotly_chart(px.line(df,x="timestamp",y="score",title=f"{selected} Performance"),use_container_width=True)
            else:
                st.info(f"No scores for {selected} yet.")
    
    st.markdown("### 📝 New Score")
    with st.form("record_score"):
        topic=st.selectbox("Topic",list(topics) if topics else ["No topics"])
        score=st.slider("Score",0,100,75)
        if st.form_submit_button("Record") and topic!="No topics":
            memory.record_performance(topic,score)
            memory.save_memory()
            st.success(f"Score recorded: {score}")
            st.rerun()

with tab3:
    st.markdown("### 🧠 Working Memory State")
    
    c1,c2=st.columns(2)
    with c1:
        st.info(f"ID: {st.session_state.student_id}")
        if st.button("Reset"):
            st.session_state.memory=WorkingMemory(student_id=st.session_state.student_id)
            st.success("Memory reset")
            st.rerun()
    
    with c2:
        sessions=len(memory.session_history)
        records=sum(len(r) for r in memory.performance_history.values())
        st.metric("Sessions",sessions)
        st.metric("Records",records)
