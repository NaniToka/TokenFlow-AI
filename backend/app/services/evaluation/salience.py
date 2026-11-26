"""
Token-Level Salience Heat-Map Scorer.

Assigns normalized [0.0, 1.0] information-density weights to individual words/tokens
based on query alignment, technical entity morphology, and stopword suppression.
"""

from __future__ import annotations

import re
from typing import Any

STOPWORDS = {
    "the", "and", "is", "in", "to", "of", "it", "you", "that", "was", "for",
    "on", "are", "as", "with", "they", "at", "be", "this", "have", "from",
    "or", "by", "an", "we", "our", "can", "will", "what", "how", "why", "a",
}


def compute_token_salience(text: str, query: str = "") -> list[dict[str, Any]]:
    """
    Score each token in `text` for visualization as a semantic heat-map.

    Returns:
        List of {token, weight, category} where category is 'query_match' | 'entity' | 'content' | 'filler'.
    """
    if not text:
        return []

    query_terms = set(re.findall(r"[a-z0-9_]+", query.lower())) - STOPWORDS
    words = text.split()
    scored: list[dict[str, Any]] = []

    for raw in words[:300]:  # cap for fast UI rendering
        clean = re.sub(r"[^\w\-./:]", "", raw)
        low = clean.lower()

        if not clean or low in STOPWORDS:
            weight = 0.12
            cat = "filler"
        elif low in query_terms:
            weight = 0.98
            cat = "query_match"
        elif re.match(r"^(?:[A-Z][a-zA-Z0-9]+|[a-z]+_[a-z0-9_]+|\d+(?:\.\d+)?|`.*`)$", clean):
            weight = 0.78
            cat = "entity"
        else:
            weight = min(0.65, 0.30 + len(clean) * 0.03)
            cat = "content"

        scored.append({
            "token": raw,
            "weight": round(weight, 2),
            "category": cat,
        })

    return scored
