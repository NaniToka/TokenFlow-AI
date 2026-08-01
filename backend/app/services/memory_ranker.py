import math
import numpy as np
from typing import List, Dict, Any
from app.schemas import Turn
from app.utils.embeddings import get_embedding, get_batch_embeddings


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculates the cosine similarity between two float vectors using numpy.
    Returns a float between -1.0 and 1.0 (or 0.0 for zero vectors/empty input).
    """
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    sim = np.dot(a, b) / (norm_a * norm_b)
    return float(np.clip(sim, -1.0, 1.0))


def compute_recency_weight(index: int, total_turns: int, decay_factor: float = 0.05) -> float:
    """
    Calculates an exponential recency weight:
    exp(-decay_factor * (total_turns - 1 - index))
    The most recent turn (index == total_turns - 1) gets weight 1.0.
    Older turns decay exponentially.
    """
    if total_turns <= 0 or index < 0:
        return 0.0
    distance = total_turns - 1 - index
    weight = math.exp(-decay_factor * distance)
    return float(weight)


def _lexical_similarity(text1: str, text2: str) -> float:
    """
    Fallback Jaccard lexical similarity when vector embeddings are empty/unavailable.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0


def rank_turns(
    history: List[Turn],
    current_message: str,
    top_k: int = 3,
    alpha: float = 0.7
) -> Dict[str, Any]:
    """
    Ranks conversation history turns using a hybrid score of semantic similarity and recency.
    Operates strictly on isolated local turn data per request.
    """
    # Create an isolated local copy of input history turns
    local_history = [Turn(role=t.role, content=t.content) for t in (history or [])]
    total_turns = len(local_history)
    if total_turns == 0:
        return {
            "selected_turns": [],
            "unselected_turns": [],
            "scores": []
        }

    # Fetch embeddings
    query_vec = get_embedding(current_message)
    turn_texts = [turn.content for turn in local_history]
    turn_vecs = get_batch_embeddings(turn_texts)

    scored_items = []
    for i, turn in enumerate(local_history):
        recency_score = compute_recency_weight(i, total_turns)
        
        turn_vec = turn_vecs[i] if i < len(turn_vecs) else []
        sim_score = cosine_similarity(query_vec, turn_vec)

        # Fallback to lexical similarity if embedding is unavailable/empty
        if sim_score == 0.0 and (not query_vec or not turn_vec):
            sim_score = _lexical_similarity(current_message, turn.content)

        # Ensure non-negative similarity for weighted scoring
        sim_score_norm = max(0.0, sim_score)
        final_score = alpha * sim_score_norm + (1.0 - alpha) * recency_score

        snippet = turn.content[:60] + ("..." if len(turn.content) > 60 else "")
        scored_items.append({
            "index": i,
            "turn": turn,
            "role": turn.role,
            "content_snippet": snippet,
            "similarity": round(sim_score_norm, 4),
            "recency": round(recency_score, 4),
            "final_score": round(final_score, 4),
            "selected": False
        })

    # Sort by final score descending
    ranked_items = sorted(scored_items, key=lambda x: x["final_score"], reverse=True)

    # Select top-k turns
    k = min(top_k, total_turns)
    selected_indices = set()
    for item in ranked_items[:k]:
        item["selected"] = True
        selected_indices.add(item["index"])

    # Separate and sort by chronological index
    selected_items = sorted([item for item in scored_items if item["index"] in selected_indices], key=lambda x: x["index"])
    unselected_items = sorted([item for item in scored_items if item["index"] not in selected_indices], key=lambda x: x["index"])

    selected_turns = [item["turn"] for item in selected_items]
    unselected_turns = [item["turn"] for item in unselected_items]

    # Format scores array for API return
    scores_metadata = [
        {
            "index": item["index"],
            "role": item["role"],
            "content_snippet": item["content_snippet"],
            "similarity": item["similarity"],
            "recency": item["recency"],
            "final_score": item["final_score"],
            "selected": item["selected"]
        }
        for item in scored_items
    ]

    return {
        "selected_turns": selected_turns,
        "unselected_turns": unselected_turns,
        "scores": scores_metadata
    }
