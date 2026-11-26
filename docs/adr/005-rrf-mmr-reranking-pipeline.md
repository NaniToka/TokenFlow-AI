# ADR-005: Reciprocal Rank Fusion (RRF), MMR Diversity & N-Gram Reranking Pipeline

- **Status**: Accepted
- **Date**: 2026-11-26

## Context

Linear combination of BM25, dense cosine similarity, and exponential recency scores (`alpha * sim + (1 - alpha) * recency`) requires per-domain scale calibration because BM25 scores fluctuate wildly across conversation lengths while cosine similarities cluster tightly in `[0.2, 0.9]`. Additionally, naive Top-K selection frequently selects redundant near-identical turns, crowding out distinct technical constraints.

## Decision

We added an optional three-stage ranking extension in `backend/app/services/ranking/`:

1. **Reciprocal Rank Fusion (`fusion.py`)**: Computes `score(d) = sum(w_i / (k + rank_i(d)))` (`k = 60`) across BM25, dense semantic, and recency rankings, eliminating score-scale sensitivity.
2. **N-Gram + Identifier Reranker (`reranker.py`)**: Second-stage cross-scorer boosting bigrams and technical symbols (snake_case, CamelCase, numbers, inline code) shared with the current query.
3. **Maximal Marginal Relevance (`mmr.py`)**: Iteratively picks Top-K turns maximizing `lambda * Relevance(d, q) - (1 - lambda) * max Similarity(d, selected)` while preserving chronological order afterward.

## Consequences

- Callers choose `fusion_method: "rrf" | "linear"`, `use_mmr`, and `use_reranker` per request without reindexing or training external cross-encoder weights.
- Zero additional runtime dependencies (`numpy` / `pytorch` avoided), preserving sub-millisecond local CPU execution.
