# engine/inference.py
from engine.knowledge_base import difficulty_weights, importance_weights

def calculate_priority(topic):
    difficulty = topic["difficulty"]
    importance = topic["importance"]
    score = topic["score"]

    # Access weights from the knowledge base
    d_weight = difficulty_weights.get(difficulty, 1)
    i_weight = importance_weights.get(importance, 1)

    # Priority formula
    raw_priority = (d_weight + i_weight) * (100 - score)
    return round(raw_priority, 2)
