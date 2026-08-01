import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas import Turn
from app.services.memory_ranker import cosine_similarity, compute_recency_weight, rank_turns


def test_memory_ranker():
    print("\n--- 1. Testing Cosine Similarity & Recency Decay Math ---")
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]
    
    sim_identical = cosine_similarity(vec1, vec2)
    sim_orthogonal = cosine_similarity(vec1, vec3)
    print(f"Cosine Similarity (identical): {sim_identical}")
    print(f"Cosine Similarity (orthogonal): {sim_orthogonal}")
    assert sim_identical == 1.0
    assert sim_orthogonal == 0.0

    recency_last = compute_recency_weight(9, 10)
    recency_first = compute_recency_weight(0, 10)
    print(f"Recency Weight (latest turn index 9): {recency_last:.4f}")
    print(f"Recency Weight (first turn index 0): {recency_first:.4f}")
    assert recency_last == 1.0
    assert recency_first < recency_last

    print("\n--- 2. Testing Memory Ranker with 10-turn Conversation ---")
    mock_history = [
        Turn(role="user", content="What is the weather like in Tokyo today?"),
        Turn(role="model", content="Tokyo is sunny and 22 degrees Celsius."),
        Turn(role="user", content="Can you help me write a Python function to sort a list of dictionaries?"),
        Turn(role="model", content="Sure! You can use sorted(lst, key=lambda x: x['key'])."),
        Turn(role="user", content="I need to design a PostgreSQL database table for storing user profiles."),
        Turn(role="model", content="You can create a table users with columns id, email, created_at, and settings jsonb."),
        Turn(role="user", content="My SQL query SELECT * FROM users WHERE settings->>'theme' = 'dark' is running slowly."),
        Turn(role="model", content="You should add a GIN index or expression index on (settings->>'theme') to speed up your query."),
        Turn(role="user", content="Also, what is the best recipe for baking sourdough bread at home?"),
        Turn(role="model", content="Sourdough bread requires flour, water, salt, and active starter.")
    ]

    current_message = "How do I fix my SQL query?"
    print(f"Current Query: '{current_message}'")
    print(f"Total History Turns: {len(mock_history)}")

    result = rank_turns(mock_history, current_message, top_k=3, alpha=0.7)

    print("\n--- Ranking Results ---")
    for score in result["scores"]:
        status = "✅ SELECTED" if score["selected"] else "  UNSELECTED"
        print(f"Turn [{score['index']}] ({score['role']}) {status} | Sim: {score['similarity']} | Recency: {score['recency']} | Final: {score['final_score']}")
        print(f"    Snippet: {score['content_snippet']}")

    selected_turns = result["selected_turns"]
    unselected_turns = result["unselected_turns"]
    print(f"\nTotal Selected Turns: {len(selected_turns)}")
    print(f"Total Unselected Turns: {len(unselected_turns)}")

    assert len(selected_turns) == 3, f"Expected 3 selected turns, got {len(selected_turns)}"
    assert len(unselected_turns) == 7, f"Expected 7 unselected turns, got {len(unselected_turns)}"

    # Check if SQL related turns (turn index 6 or 7) were selected
    selected_contents = " ".join([t.content for t in selected_turns])
    print(f"\nCombined Selected Content:\n{selected_contents}")
    assert "SQL" in selected_contents or "index" in selected_contents or "table" in selected_contents, \
        "Expected database/SQL turns to be selected in top-k"

    print("\n✅ Memory Ranker test passed successfully!")


if __name__ == "__main__":
    test_memory_ranker()
