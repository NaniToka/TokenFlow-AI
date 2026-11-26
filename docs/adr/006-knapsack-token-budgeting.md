# ADR-006: Hard Token Budgeting via Knapsack Selection & Hierarchical Map-Reduce Summarization

- **Status**: Accepted
- **Date**: 2026-11-26

## Context

Fixed `top_k` selection does not bound downstream token counts when retained turns contain lengthy code snippets, stack traces, or logs. Meanwhile, compressing 20+ evicted turns in a single shot degrades extractive/LLM fidelity when intermediate context spans multiple distinct discussion phases.

## Decision

We implemented two deterministic budget-aware compression controls in `backend/app/services/compression/`:

1. **Greedy Density Knapsack (`budget_optimizer.py`)**: When `max_context_tokens` is specified, turns sorted by utility density (`ranking_score / max(1, token_count)`) are packed greedily under the remaining token allowance (reserving room for system instructions, background memory, and the current query), then re-ordered chronologically.
2. **Hierarchical Epoch Map-Reduce (`hierarchical.py`)**: When >12 turns are evicted, turns are grouped into fixed epochs (`epoch_size=6`), distilled per-epoch into compact abstracts, and rolled up into a final structured memory summary alongside `entity_extractor.py` graph nodes (`entities`, `code_symbols`, `decisions`, `open_questions`).

## Consequences

- Downstream LLM callers can enforce hard token SLAs regardless of individual turn lengths.
- Long multi-hour sessions avoid catastrophic middle-context amnesia without blocking request latency.
