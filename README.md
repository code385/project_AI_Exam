# 📘 Intelligent Exam Preparation Assistant

This AI-based expert system helps students prioritize topics and generate a personalized study plan based on:
- Performance (test scores)
- Topic difficulty
- Topic importance
- Days remaining
- Daily study hours

## 💡 Features
- Priority classification (Very High → Skip)
- Smart time allocation
- Interactive UI using Streamlit
- Pie chart visualization of study hours

## 📂 Project Structure
IntelligentExamSystem/
├── engine/
│ └── inference.py
├── utils/
│ └── scheduler.py
├── ui/
│ └── app.py
├── main.py
└── requirements.txt

## 🚀 Run Locally
```bash
pip install -r requirements.txt
streamlit run ui/app.py