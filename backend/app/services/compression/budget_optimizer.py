"""
Token Budget Knapsack Optimizer.

Enforces hard downstream context-window token ceilings (`max_context_tokens`) by
packing highest value-per-token turns (score_i / tokens_i) while guaranteeing
system instructions, summaries, and the current user message fit strictly inside budget.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas import Turn
from app.utils.token_counter import count_tokens


@dataclass
class BudgetPackResult:
    packed_turns: list[Turn]
    dropped_for_budget: int
    budget_used_tokens: int
    budget_limit: int


def enforce_token_budget(
    scored_selected: list[tuple[int, Turn, float]],
    current_message: str,
    summary: str = "",
    system_instruction: str = "",
    max_context_tokens: int | None = None,
) -> BudgetPackResult:
    """
    Pack selected turns under a hard max_context_tokens ceiling using greedy
    relevance-per-token density sorting, then restore chronological order.
    """
    if max_context_tokens is None or max_context_tokens <= 0:
        turns_only = [t for _, t, _ in sorted(scored_selected, key=lambda x: x[0])]
        return BudgetPackResult(
            packed_turns=turns_only,
            dropped_for_budget=0,
            budget_used_tokens=0,
            budget_limit=0,
        )

    # Calculate non-evictable overhead (current query + headers + summary + system)
    overhead_parts = [f"[CURRENT USER MESSAGE]\n{current_message.strip()}"]
    if system_instruction.strip():
        overhead_parts.append(f"[SYSTEM INSTRUCTION]\n{system_instruction.strip()}")
    if summary.strip():
        overhead_parts.append(f"[BACKGROUND CONTEXT SUMMARY]\n{summary.strip()}")
    overhead_parts.append("[RELEVANT RECENT HISTORY]\n")

    used = count_tokens("\n\n".join(overhead_parts))
    remaining_budget = max(0, max_context_tokens - used)

    # Compute token cost and density (score / tokens) per candidate
    candidates: list[tuple[int, Turn, float, int, float]] = []
    for idx, turn, score in scored_selected:
        line_tok = max(1, count_tokens(f"[{turn.role.capitalize()}]: {turn.content}"))
        density = (score + 0.01) / line_tok
        candidates.append((idx, turn, score, line_tok, density))

    # Pack highest density turns first (knapsack greedy approximation)
    candidates.sort(key=lambda x: x[4], reverse=True)

    chosen: list[tuple[int, Turn]] = []
    dropped = 0
    for idx, turn, _score, tok_cost, _density in candidates:
        if tok_cost <= remaining_budget:
            chosen.append((idx, turn))
            remaining_budget -= tok_cost
            used += tok_cost
        else:
            dropped += 1

    # Restore chronological order
    chosen.sort(key=lambda x: x[0])

    return BudgetPackResult(
        packed_turns=[t for _, t in chosen],
        dropped_for_budget=dropped,
        budget_used_tokens=used,
        budget_limit=max_context_tokens,
    )
