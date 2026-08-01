import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.token_counter import count_tokens, calculate_gemini_cost, calculate_savings
from app.utils.embeddings import get_embedding, get_batch_embeddings
from app.config import settings


def test_token_counter():
    print("\n--- 1. Testing Token Counter & Cost Utilities ---")
    sample_text = "TokenFlow AI is a production-grade Prompt Memory Optimizer middleware."
    tokens = count_tokens(sample_text)
    print(f"Sample Text: '{sample_text}'")
    print(f"Token Count: {tokens} tokens")
    assert tokens > 0, "Token count should be greater than 0"

    # Test cost calculation
    cost_input = calculate_gemini_cost(tokens, is_input=True)
    cost_output = calculate_gemini_cost(tokens, is_input=False)
    print(f"Cost for {tokens} input tokens: ${cost_input:.8f}")
    print(f"Cost for {tokens} output tokens: ${cost_output:.8f}")
    assert cost_input > 0, "Input cost should be greater than 0"
    assert cost_output > cost_input, "Output cost rate is higher than input cost rate"

    # Test savings calculation
    original = 1000
    compressed = 300
    savings = calculate_savings(original, compressed)
    print(f"Savings Test (Original: {original}, Compressed: {compressed}):")
    print(f"  - Tokens Saved: {savings['tokens_saved']}")
    print(f"  - Compression Ratio: {savings['compression_ratio']}%")
    print(f"  - Cost Before: ${savings['cost_before_usd']:.8f}")
    print(f"  - Cost After: ${savings['cost_after_usd']:.8f}")
    print(f"  - Cost Saved: ${savings['cost_saved_usd']:.8f}")

    assert savings['tokens_saved'] == 700
    assert savings['compression_ratio'] == 70.0
    assert savings['cost_saved_usd'] > 0
    print("✅ Token Counter & Cost test passed!")


def test_embeddings():
    print("\n--- 2. Testing Gemini Embeddings Client ---")
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠️ GEMINI_API_KEY is not configured in backend/.env. Skipping live API call.")
        print("Note: Set GEMINI_API_KEY in backend/.env to run live embedding test.")
        return

    sample_query = "What is prompt engineering and semantic search?"
    print(f"Sending embedding request for: '{sample_query}'")
    embedding = get_embedding(sample_query)
    
    if embedding:
        print(f"✅ Received embedding vector successfully!")
        print(f"   - Vector dimension (length): {len(embedding)}")
        print(f"   - Sample values (first 5): {embedding[:5]}")
        assert len(embedding) == 768, f"Expected 768 dimensions for text-embedding-004, got {len(embedding)}"
    else:
        print("❌ Failed to retrieve embedding. Check GEMINI_API_KEY or network connection.")

    # Test batch embeddings
    batch_texts = ["First turn in conversation.", "Second turn in conversation."]
    print(f"\nSending batch embedding request for {len(batch_texts)} texts...")
    batch_vecs = get_batch_embeddings(batch_texts)
    print(f"   - Received batch vectors: {len(batch_vecs)}")
    if batch_vecs and len(batch_vecs) > 0 and batch_vecs[0]:
        print(f"   - First vector dimension: {len(batch_vecs[0])}")
        print("✅ Batch embedding test passed!")


if __name__ == "__main__":
    test_token_counter()
    test_embeddings()
