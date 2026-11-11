"""
TokenFlow-AI Compression & Latency Benchmark Suite.
Measures execution time percentiles (p50, p90, p99), token compression ratios,
and cost reduction across conversation history tiers.
"""

import os
import sys
import time
import json
import statistics
from typing import List, Dict, Any

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.insert(0, backend_dir)

from app.schemas import CompressRequest, Turn
from app.services.assembler import process_compression
from app.utils.token_counter import calculate_gemini_cost


def generate_synthetic_dialogue(turns_count: int) -> List[Turn]:
    """Generates realistic alternating user/model dialogue turns."""
    topics = [
        ("How do I set up a PostgreSQL database on Google Cloud Run?", "You can deploy Cloud SQL and configure Unix domain socket connections."),
        ("What about connection pooling?", "You should use Cloud SQL Auth Proxy or PgBouncer to manage connection limits."),
        ("Can we add an index to user_id?", "Yes, run CREATE INDEX CONCURRENTLY idx_user_id ON users(user_id); to avoid locking."),
        ("How do we handle migrations in CI/CD?", "Run Flyway or Alembic inside a Cloud Build or GitHub Actions deployment step."),
        ("What about backup retention policy?", "Configure automated daily backups with a 7-day retention window in Cloud SQL settings."),
    ]
    turns = []
    for i in range(turns_count):
        user_msg, model_msg = topics[i % len(topics)]
        turns.append(Turn(role="user", content=f"Step {i+1}: {user_msg}"))
        turns.append(Turn(role="model", content=f"Response {i+1}: {model_msg}"))
    return turns


def run_latency_benchmark(runs_per_tier: int = 20) -> Dict[str, Any]:
    tiers = [10, 25, 50, 100]
    tier_results = {}

    for turn_count in tiers:
        history = generate_synthetic_dialogue(turn_count // 2)
        current = "How do we verify the connection pool latency?"
        req = CompressRequest(
            system_instruction="You are an enterprise cloud database expert.",
            history=history,
            current_message=current,
            top_k=3,
        )

        latencies_ms = []
        original_tokens = 0
        compressed_tokens = 0

        for _ in range(runs_per_tier):
            start = time.perf_counter()
            resp = process_compression(req)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latencies_ms.append(elapsed_ms)
            original_tokens = resp.original_tokens
            compressed_tokens = resp.compressed_tokens

        latencies_ms.sort()
        p50 = statistics.median(latencies_ms)
        p90 = latencies_ms[int(0.90 * len(latencies_ms))]
        p99 = latencies_ms[int(0.99 * len(latencies_ms))]
        reduction_pct = ((original_tokens - compressed_tokens) / original_tokens) * 100.0 if original_tokens > 0 else 0.0

        cost_orig = calculate_gemini_cost(original_tokens, is_input=True)
        cost_comp = calculate_gemini_cost(compressed_tokens, is_input=True)

        tier_results[f"{turn_count}_turns"] = {
            "turns": turn_count,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_percentage": round(reduction_pct, 2),
            "p50_latency_ms": round(p50, 3),
            "p90_latency_ms": round(p90, 3),
            "p99_latency_ms": round(p99, 3),
            "cost_before_usd": cost_orig,
            "cost_after_usd": cost_comp,
        }

    return tier_results


if __name__ == "__main__":
    print("Executing TokenFlow Latency & Cost Benchmark...")
    results = run_latency_benchmark()
    print(json.dumps(results, indent=2))
