import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas import Turn
from app.services.compressor import summarize_turns
from app.utils.token_counter import count_tokens, calculate_savings


def test_compressor():
    print("\n--- Testing Context Compressor Service ---")
    
    mock_unselected = [
        Turn(role="user", content="I am building a web application called HealthPulse for digital healthcare."),
        Turn(role="model", content="That sounds great! What is the primary purpose of HealthPulse?"),
        Turn(role="user", content="It is a patient monitoring dashboard for tracking real-time vital signs and heart rate data."),
        Turn(role="model", content="Got it. What technology stack are you planning to use for frontend and backend?"),
        Turn(role="user", content="We decided to use React with TypeScript for frontend and FastAPI with PostgreSQL for backend."),
        Turn(role="model", content="Excellent tech stack choice! Are there any specific compliance requirements like HIPAA?"),
        Turn(role="user", content="Yes, strict HIPAA compliance is mandatory, including end-to-end data encryption at rest and in transit."),
        Turn(role="model", content="Understood. All architecture recommendations will strictly adhere to HIPAA compliance and encryption standards.")
    ]

    original_text = "\n".join([f"[{t.role}]: {t.content}" for t in mock_unselected])
    original_tokens = count_tokens(original_text)

    print(f"Total Unselected Turns: {len(mock_unselected)}")
    print(f"Original Text Token Count: {original_tokens} tokens")

    summary = summarize_turns(mock_unselected)
    summary_tokens = count_tokens(summary)

    print("\n--- Generated Summary ---")
    print(summary)
    print("-------------------------")
    print(f"Summary Token Count: {summary_tokens} tokens")

    savings = calculate_savings(original_tokens, summary_tokens)
    print("\n--- Compression Metrics ---")
    print(f"Tokens Saved: {savings['tokens_saved']}")
    print(f"Compression Ratio: {savings['compression_ratio']}%")
    print(f"Cost Saved (Input): ${savings['cost_saved_usd']:.8f}")

    assert len(summary) > 0, "Summary should not be empty"
    assert summary_tokens < original_tokens, "Summary token count should be less than original token count"
    print("\n✅ Context Compressor test passed successfully!")


if __name__ == "__main__":
    test_compressor()
