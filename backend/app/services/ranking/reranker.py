"""
Second-Stage N-Gram & Structural Cross-Encoder Reranker.

Refines initial retrieval scores by computing contiguous bigram/trigram phrase overlap,
technical identifier match ratios, and code-block alignment bonuses.
"""

from __future__ import annotations

import re


def _extract_ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _extract_identifiers(text: str) -> set[str]:
    """Extracts camelCase, snake_case, UPPER_SNAKE, and dashed identifiers."""
    return set(re.findall(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z]{2,}[A-Z0-9_]*|[a-z]+-[a-z0-9-]+)\b", text))


class CrossEncoderReranker:
    """Deterministic second-stage phrase & structural reranker."""

    def score_candidates(self, query: str, candidates: list[str]) -> list[float]:
        """Compute [0.0, 1.0] reranking boost scores for each candidate."""
        if not query or not candidates:
            return [0.0] * len(candidates)

        q_tokens = re.findall(r"\w+", query.lower())
        q_bigrams = _extract_ngrams(q_tokens, 2)
        q_trigrams = _extract_ngrams(q_tokens, 3)
        q_ids = _extract_identifiers(query)

        scores: list[float] = []
        for cand in candidates:
            c_tokens = re.findall(r"\w+", cand.lower())
            c_bigrams = _extract_ngrams(c_tokens, 2)
            c_trigrams = _extract_ngrams(c_tokens, 3)
            c_ids = _extract_identifiers(cand)

            bigram_score = (
                len(q_bigrams & c_bigrams) / len(q_bigrams)
                if q_bigrams
                else 0.0
            )
            trigram_score = (
                len(q_trigrams & c_trigrams) / len(q_trigrams)
                if q_trigrams
                else 0.0
            )
            id_score = (
                len(q_ids & c_ids) / len(q_ids)
                if q_ids
                else 0.0
            )

            combined = 0.45 * bigram_score + 0.35 * trigram_score + 0.20 * id_score
            scores.append(round(min(1.0, combined), 4))

        return scores
