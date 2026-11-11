import pytest
from app.schemas import Turn
from app.services.memory_ranker import cosine_similarity, compute_recency_weight, _lexical_similarity, rank_turns
from app.utils.embeddings import batch_cosine_similarity_matrix
from app.utils.token_counter import count_tokens, calculate_gemini_cost


def test_batch_cosine_similarity_matrix():
    query = [1.0, 0.0, 0.0]
    candidates = [
        [1.0, 0.0, 0.0],   # Identical -> 1.0
        [0.0, 1.0, 0.0],   # Orthogonal -> 0.0
        [-1.0, 0.0, 0.0],  # Opposite -> -1.0
        [],                # Empty -> 0.0
    ]
    scores = batch_cosine_similarity_matrix(query, candidates)
    assert len(scores) == 4
    assert pytest.approx(scores[0], 0.001) == 1.0
    assert pytest.approx(scores[1], 0.001) == 0.0
    assert pytest.approx(scores[2], 0.001) == -1.0
    assert scores[3] == 0.0


def test_cosine_similarity():
    # Identical vectors
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0
    # Orthogonal vectors
    assert cosine_similarity([1, 0, 0], [0, 1, 0]) == 0.0
    # Opposite vectors
    assert cosine_similarity([1, 0, 0], [-1, 0, 0]) == -1.0
    # Empty vectors
    assert cosine_similarity([], []) == 0.0

def test_compute_recency_weight():
    # Latest turn should have weight 1.0
    assert compute_recency_weight(index=4, total_turns=5, decay_factor=0.1) == 1.0
    # Older turns should have weight < 1.0
    assert compute_recency_weight(index=0, total_turns=5, decay_factor=0.1) < 1.0

def test_lexical_similarity():
    assert _lexical_similarity("hello world", "hello world") == 1.0
    assert _lexical_similarity("hello world", "goodbye earth") == 0.0
    assert _lexical_similarity("hello world", "hello friend") > 0.0

def test_rank_turns():
    history = [
        Turn(role="user", content="How do I install python?"),
        Turn(role="model", content="You can download it from python.org"),
        Turn(role="user", content="What is Kubernetes?"),
        Turn(role="model", content="It's a container orchestration platform.")
    ]
    current = "Tell me more about pods in k8s."
    
    # rank_turns uses fallback lexical similarity since we have no API key
    result = rank_turns(history, current, top_k=2)
    
    assert len(result["selected_turns"]) == 2
    assert len(result["unselected_turns"]) == 2
    # The most recent turns should have higher recency score, so even without good lexical match, they should rank higher.
    assert result["scores"][-1]["index"] == 3

def test_token_counter():
    text = "Hello world, this is a test."
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)
