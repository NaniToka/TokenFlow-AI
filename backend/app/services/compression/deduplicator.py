"""
Semantic Deduplication & Near-Duplicate Turn Collapser.

Detects repeated retries, duplicate user queries, and boilerplate model apologies
using normalized token-set Jaccard overlap, collapsing redundant turns while preserving
the latest occurrence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import Turn


@dataclass
class DeduplicationResult:
    deduplicated_turns: list[Turn]
    duplicates_removed: int


def _norm_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def deduplicate_turns(
    turns: list[Turn],
    similarity_threshold: float = 0.85,
) -> DeduplicationResult:
    """
    Remove near-duplicate turns of the same role, retaining the most recent instance.

    Args:
        turns: Chronological turn list.
        similarity_threshold: Jaccard threshold above which an older identical-role turn is dropped.
    """
    if len(turns) <= 1:
        return DeduplicationResult(deduplicated_turns=list(turns), duplicates_removed=0)

    # Walk backwards so the newest version of a duplicate turn is always retained
    kept_reversed: list[Turn] = []
    seen_by_role: dict[str, list[set[str]]] = {"user": [], "model": []}
    removed = 0

    for turn in reversed(turns):
        tokens = _norm_tokens(turn.content)
        is_dup = False
        if tokens:
            for existing_tokens in seen_by_role.get(turn.role, []):
                union = tokens | existing_tokens
                sim = len(tokens & existing_tokens) / len(union) if union else 0.0
                if sim >= similarity_threshold:
                    is_dup = True
                    break

        if is_dup:
            removed += 1
        else:
            seen_by_role.setdefault(turn.role, []).append(tokens)
            kept_reversed.append(turn)

    kept_reversed.reverse()
    return DeduplicationResult(
        deduplicated_turns=kept_reversed,
        duplicates_removed=removed,
    )
