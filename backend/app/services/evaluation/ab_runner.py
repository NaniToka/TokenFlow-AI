"""
A/B Strategy Experiment Runner.

Executes two distinct compression configurations (Variant A vs Variant B) against
the exact same conversation history and compares token savings, USD savings,
quality fidelity score, and execution latency to select an empirical winner.
"""

from __future__ import annotations

from typing import Any

from app.schemas import CompressRequest, Turn
from app.services.evaluation.evaluator import ContextQualityEvaluator


def run_ab_experiment(
    pipeline: Any,
    evaluator: ContextQualityEvaluator,
    history: list[Turn],
    current_message: str,
    variant_a: dict[str, Any],
    variant_b: dict[str, Any],
) -> dict[str, Any]:
    """Run Variant A and Variant B side-by-side and return empirical deltas."""

    def _build_req(cfg: dict[str, Any]) -> CompressRequest:
        return CompressRequest(
            history=history,
            current_message=current_message,
            top_k=int(cfg.get("top_k", 3)),
            alpha=cfg.get("alpha"),
            target_model=str(cfg.get("target_model", "gemini-1.5-flash")),
            compression_mode=cfg.get("compression_mode", "balanced"),
            fusion_method=str(cfg.get("fusion_method", "linear")),
            use_mmr=bool(cfg.get("use_mmr", False)),
            use_reranker=bool(cfg.get("use_reranker", False)),
            max_context_tokens=cfg.get("max_context_tokens"),
            use_cache=False,
        )

    res_a = pipeline.compress(_build_req(variant_a))
    res_b = pipeline.compress(_build_req(variant_b))

    eval_a = evaluator.evaluate(history, res_a)
    eval_b = evaluator.evaluate(history, res_b)

    # Composite utility: 60% semantic fidelity + 40% token compression ratio
    utility_a = 0.6 * eval_a.semantic_fidelity + 0.4 * res_a.compression_ratio
    utility_b = 0.6 * eval_b.semantic_fidelity + 0.4 * res_b.compression_ratio

    winner = "Variant A" if utility_a >= utility_b else "Variant B"

    return {
        "winner": winner,
        "delta": {
            "tokens_saved_diff": res_b.tokens_saved - res_a.tokens_saved,
            "compression_ratio_diff": round(res_b.compression_ratio - res_a.compression_ratio, 2),
            "fidelity_diff": round(eval_b.semantic_fidelity - eval_a.semantic_fidelity, 2),
            "latency_diff_ms": round(res_b.metadata.latency_ms - res_a.metadata.latency_ms, 2),
        },
        "variant_a": {
            "config": variant_a,
            "tokens_saved": res_a.tokens_saved,
            "compression_ratio": res_a.compression_ratio,
            "semantic_fidelity": eval_a.semantic_fidelity,
            "composite_grade": eval_a.composite_grade,
            "latency_ms": res_a.metadata.latency_ms,
            "strategy": res_a.metadata.ranking_strategy,
        },
        "variant_b": {
            "config": variant_b,
            "tokens_saved": res_b.tokens_saved,
            "compression_ratio": res_b.compression_ratio,
            "semantic_fidelity": eval_b.semantic_fidelity,
            "composite_grade": eval_b.composite_grade,
            "latency_ms": res_b.metadata.latency_ms,
            "strategy": res_b.metadata.ranking_strategy,
        },
    }
