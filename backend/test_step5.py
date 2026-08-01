import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app


def test_compress_api():
    print("\n--- Testing /api/v1/compress End-to-End API Endpoint ---")
    client = TestClient(app)

    # Construct 15-turn conversation history
    history = [
        {"role": "user", "content": "I am working on an e-commerce platform called ShopSphere."},
        {"role": "model", "content": "Nice! What stack are you using for ShopSphere?"},
        {"role": "user", "content": "We use Next.js 14, Tailwind CSS, FastAPI, and MongoDB."},
        {"role": "model", "content": "Solid tech stack! Are you using MongoDB Atlas or self-hosted?"},
        {"role": "user", "content": "We are using MongoDB Atlas with M10 cluster tier."},
        {"role": "model", "content": "Got it. How are you handling authentication?"},
        {"role": "user", "content": "We use Clerk for user auth and JWT validation in FastAPI."},
        {"role": "model", "content": "Understood. How about payment processing integration?"},
        {"role": "user", "content": "Stripe API with webhooks for handling subscriptions and orders."},
        {"role": "model", "content": "Cool! Are there any performance bottlenecks currently?"},
        {"role": "user", "content": "Product search query response time is around 1.2 seconds, which is too slow."},
        {"role": "model", "content": "You can add text indexing in MongoDB or integrate Elasticsearch / Algolia."},
        {"role": "user", "content": "We decided to implement MongoDB Atlas Search index on title and description fields."},
        {"role": "model", "content": "Atlas Search is a great choice! You can use $search aggregation pipeline stage."},
        {"role": "user", "content": "What is the optimal aggregation pipeline query structure for MongoDB Atlas Search?"}
    ]

    current_message = "Can you write an example FastAPI route demonstrating MongoDB Atlas Search with pagination?"

    payload = {
        "history": history,
        "current_message": current_message,
        "top_k": 3
    }

    print(f"Sending payload with {len(history)} history turns and query: '{current_message}'")
    response = client.post("/api/v1/compress", json=payload)

    print(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    print("\n--- API Response Highlights ---")
    print(f"Summary:\n{data['summary']}\n")
    print(f"Selected Turns ({len(data['selected_turns'])}):")
    for turn in data["selected_turns"]:
        print(f"  - [{turn['role']}]: {turn['content'][:60]}...")
    
    print("\nFinal Prompt Preview:")
    print("-" * 50)
    print(data["final_prompt"])
    print("-" * 50)

    print("\nToken & Cost Savings Metrics:")
    print(f"  Original Tokens:   {data['original_tokens']}")
    print(f"  Compressed Tokens: {data['compressed_tokens']}")
    print(f"  Tokens Saved:      {data['tokens_saved']}")
    print(f"  Compression Ratio: {data['compression_ratio']}%")
    print(f"  Cost Before:       ${data['cost_before_usd']:.8f}")
    print(f"  Cost After:        ${data['cost_after_usd']:.8f}")
    print(f"  Cost Saved:        ${data['cost_saved_usd']:.8f}")

    assert data["original_tokens"] > data["compressed_tokens"]
    assert data["tokens_saved"] > 0
    assert data["compression_ratio"] > 0
    assert len(data["selected_turns"]) <= 3
    print("\n✅ End-to-End API test passed successfully!")


if __name__ == "__main__":
    test_compress_api()
