"""
Needle-in-a-Haystack Multi-Turn Context Stress Test Generator.

Generates synthetic multi-turn technical + noise dialogues of configurable depth,
inserts a critical secret fact ("needle") at a chosen position (e.g. 10%, 50%, 90%),
and evaluates whether TokenFlow retains or surfaces it inside the compressed prompt.
"""

from __future__ import annotations

from typing import Any

from app.schemas import CompressionMode, CompressRequest, Turn

HAYSTACK_FILLER = [
    ("user", "Can we review the quarterly deployment checklist for microservice logging?"),
    ("model", "Yes, ensure structured JSON logs are emitted to stdout and scraped by FluentBit."),
    ("user", "What did we agree on for team coffee machine maintenance on Friday?"),
    ("model", "The office facilities team handles filter replacements every Friday morning."),
    ("user", "How should we configure HTTP keep-alive timeouts on the Nginx reverse proxy?"),
    ("model", "Set `keepalive_timeout 65s;` and `proxy_read_timeout 120s;` for upstream API calls."),
    ("user", "By the way, what time does the evening shuttle depart from Building 4?"),
    ("model", "Shuttles depart every 20 minutes from Building 4 starting at 5:00 PM."),
    ("user", "Should we enforce TLS 1.3 across all internal gRPC service meshes?"),
    ("model", "Yes, Istio mTLS STRICT mode guarantees encrypted inter-pod communication."),
    ("user", "Did anyone check the cafeteria menu for Thursday lunch?"),
    ("model", "I don't have live cafeteria menus, though Mediterranean bowls are usually popular."),
]


def run_needle_in_haystack_test(
    pipeline: Any,
    haystack_turns: int = 20,
    needle_depth_pct: int = 25,
    top_k: int = 3,
    fusion_method: str = "rrf",
    compression_mode: str = "balanced",
) -> dict[str, Any]:
    """
    Inject a unique verifiable needle at `needle_depth_pct` of a multi-turn haystack
    and measure recall, token reduction, and latency.
    """
    needle_code = "TF-NEEDLE-8492"
    needle_turn = Turn(
        role="user",
        content=(
            f"CRITICAL PRODUCTION CONSTRAINT: Database failover token is {needle_code} "
            "and primary shard replica runs on port 6432 with PgBouncer transaction pooling."
        ),
    )
    needle_ack = Turn(
        role="model",
        content=f"Understood. Recorded failover token {needle_code} for shard replica port 6432.",
    )

    total_filler = max(4, min(60, haystack_turns))
    turns: list[Turn] = []
    for i in range(total_filler):
        role, content = HAYSTACK_FILLER[i % len(HAYSTACK_FILLER)]
        turns.append(Turn(role=role, content=f"[Turn {i + 1}] {content}"))

    insert_idx = max(0, min(len(turns), int((needle_depth_pct / 100.0) * len(turns))))
    turns.insert(insert_idx, needle_ack)
    turns.insert(insert_idx, needle_turn)

    query = f"What is the database failover token and port for primary shard replica ({needle_code})?"

    try:
        mode = CompressionMode(compression_mode)
    except ValueError:
        mode = CompressionMode.BALANCED

    req = CompressRequest(
        history=turns,
        current_message=query,
        top_k=top_k,
        compression_mode=mode,
        fusion_method=fusion_method,
    )
    res = pipeline.compress(req)

    needle_retained_in_prompt = needle_code in res.final_prompt
    needle_in_selected = any(needle_code in t.content for t in res.selected_turns)
    needle_in_summary = needle_code in res.summary

    return {
        "needle_code": needle_code,
        "haystack_turns": len(turns),
        "needle_turn_index": insert_idx,
        "needle_depth_pct": needle_depth_pct,
        "needle_retained": needle_retained_in_prompt,
        "retained_via": (
            "selected_turns" if needle_in_selected else
            "background_summary" if needle_in_summary else
            "evicted"
        ),
        "original_tokens": res.original_tokens,
        "compressed_tokens": res.compressed_tokens,
        "compression_ratio": res.compression_ratio,
        "latency_ms": res.metadata.latency_ms,
        "ranking_strategy": res.metadata.ranking_strategy,
    }
