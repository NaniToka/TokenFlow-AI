"""
TokenFlow-AI Interactive Quickstart Example.
Demonstrates client integration, prompt compression, and token/cost savings reporting.
"""

import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.insert(0, backend_dir)

from app.client import TokenFlowClient


def main():
    print("=" * 60)
    print("TokenFlow-AI Python SDK Quickstart Example")
    print("=" * 60)

    # Initialize client (defaults to http://localhost:8000)
    with TokenFlowClient() as client:
        # 1. Check Server Liveness
        try:
            health = client.health()
            print(f"Server Status: {health.get('status')} (v{health.get('version')})")
        except Exception as e:
            print(f"Note: Could not reach live server at localhost:8000 ({e}).")
            print("Make sure TokenFlow server is running: uvicorn app.main:app --port 8000\n")
            return

        # 2. Prepare Sample Multi-Turn Dialogue
        sample_history = [
            {"role": "user", "content": "How do I configure Redis Sentinel for high availability?"},
            {"role": "model", "content": "Deploy at least three Sentinel instances across separate nodes with quorum 2."},
            {"role": "user", "content": "What happens during a master failover?"},
            {"role": "model", "content": "Sentinels elect a leader via Raft-like voting, select the replica with lowest replication offset, and promote it."},
            {"role": "user", "content": "Can we configure client libraries to auto-discover the new master?"},
            {"role": "model", "content": "Yes, configure your Redis client with sentinel addresses instead of a fixed master host."},
        ]

        query = "How do we monitor replication lag between master and replica?"

        print("\nCompressing multi-turn conversation...")
        result = client.compress(
            history=sample_history,
            current_message=query,
            top_k=2,
            alpha=0.7,
        )

        print("\n" + "-" * 60)
        print("COMPRESSION SUMMARY")
        print("-" * 60)
        print(f"Original Input Tokens  : {result['original_tokens']}")
        print(f"Compressed Input Tokens: {result['compressed_tokens']}")
        print(f"Tokens Saved           : {result['tokens_saved']}")
        print(f"Compression Ratio      : {result['compression_ratio']}%")
        print(f"Cost Saved (USD)       : ${result['cost_saved_usd']:.8f}")
        print("-" * 60)
        print("\nFINAL OPTIMIZED PROMPT:")
        print(result["final_prompt"])


if __name__ == "__main__":
    main()
