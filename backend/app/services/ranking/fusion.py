"""
Reciprocal Rank Fusion (RRF) Scorer.

Implements Cormack, Clarke & Buettcher (2009) Reciprocal Rank Fusion:
    RRF(d) = sum(1 / (k + rank_i(d)))
to fuse heterogeneous retrieval signals (BM25, dense embeddings, recency)
without brittle linear score calibration.
"""

from __future__ import annotations


def compute_rrf_scores(
    score_lists: list[list[float]],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[float]:
    """
    Fuse multiple parallel score lists into normalized [0, 1] RRF scores.

    Args:
        score_lists: Parallel lists where score_lists[m][i] is signal m's score for item i.
        k: Smoothing constant (default 60 per Cormack et al.).
        weights: Optional per-signal multiplier weights.

    Returns:
        Normalized fused scores in [0.0, 1.0] preserving item order.
    """
    if not score_lists or not score_lists[0]:
        return []

    n_items = len(score_lists[0])
    n_signals = len(score_lists)
    sig_weights = weights if weights and len(weights) == n_signals else [1.0] * n_signals

    rrf_totals = [0.0] * n_items

    for m, scores in enumerate(score_lists):
        if len(scores) != n_items:
            continue
        # Rank item indices by descending signal score
        ranked_indices = sorted(range(n_items), key=lambda idx: scores[idx], reverse=True)
        w = sig_weights[m]
        for rank_0, item_idx in enumerate(ranked_indices):
            rank_1 = rank_0 + 1
            rrf_totals[item_idx] += w * (1.0 / (k + rank_1))

    max_score = max(rrf_totals) if rrf_totals else 0.0
    if max_score > 0:
        return [round(s / max_score, 4) for s in rrf_totals]
    return [0.0] * n_items
