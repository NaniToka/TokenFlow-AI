# ADR-001: Hybrid BM25 & Dense Vector Ranking Engine

## Context
Standard prompt compression approaches rely solely on dense semantic embeddings (cosine similarity) or basic recency slicing. Pure semantic similarity often prioritizes conceptually related turns that lack exact technical keyword matches (e.g., error codes, function signatures, specific IDs). Conversely, pure recency risks dropping foundational system specifications established early in the conversation.

## Decision
We implemented a multi-strategy ranking engine combining:
1. **Okapi BM25 Sparse Retrieval** ($k_1=1.5, b=0.75$) for exact keyword and identifier matching.
2. **Dense Vector Embeddings** (Gemini `text-embedding-004`) for conceptual similarity.
3. **Exponential Recency Weighting** with tunable half-life decay.
4. **Conversational Drift Detection** using windowed Jaccard metrics to penalize conversational tangents.
5. **Adaptive Alpha Tuning** dynamically adjusting the semantic-vs-recency balance based on dialogue length and topic consistency.

## Consequences
- **Positive**: Eliminates blind spots where technical IDs are missed by dense embeddings.
- **Positive**: Substantially reduces token waste on conversational chit-chat via drift penalties.
- **Trade-off**: Requires running both sparse and dense scoring, adding ~3-5ms compute overhead, which is negligible compared to network LLM calls.
