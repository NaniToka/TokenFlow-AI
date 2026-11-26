"""
Maximal Marginal Relevance (MMR) Diversity Reranker.

Prevents near-duplicate turns or RAG chunks from dominating top-K slots by
balancing query relevance against maximum pairwise similarity to already-selected items:
    MMR(d_i) = lambda * Rel(d_i, q) - (1 - lambda) * max_{d_j in S} Sim(d_i, d_j)
"""

from __future__ import annotations

import re


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _pairwise_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union) if union else 0.0


def mmr_select_indices(
    texts: list[str],
    relevance_scores: list[float],
    top_k: int,
    lambda_mult: float = 0.7,
) -> list[int]:
    """
    Select top_k item indices maximizing Maximal Marginal Relevance.

    Args:
        texts: Candidate text strings.
        relevance_scores: Pre-computed relevance score per candidate.
        top_k: Maximum number of indices to select.
        lambda_mult: Trade-off in [0, 1]; 1.0 = pure relevance, 0.0 = pure diversity.

    Returns:
        Selected indices ordered chronologically (ascending).
    """
    n = len(texts)
    if n == 0 or top_k <= 0:
        return []

    k = min(top_k, n)
    lam = max(0.0, min(1.0, lambda_mult))
    token_sets = [_token_set(t) for t in texts]

    remaining = list(range(n))
    selected: list[int] = []

    # First pick: highest pure relevance
    first_idx = max(remaining, key=lambda i: relevance_scores[i])
    selected.append(first_idx)
    remaining.remove(first_idx)

    while len(selected) < k and remaining:
        best_idx = remaining[0]
        best_mmr = float("-inf")

        for idx in remaining:
            rel = relevance_scores[idx]
            max_sim = max(
                _pairwise_jaccard(token_sets[idx], token_sets[sel_idx])
                for sel_idx in selected
            )
            mmr_score = lam * rel - (1.0 - lam) * max_sim
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    return sorted(selected)
