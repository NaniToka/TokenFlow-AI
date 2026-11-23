# ADR-003: Real-Time WebSocket Streaming Protocol

## Context
Large conversation histories (50+ turns) undergoing multi-stage ranking and LLM summarization can take 300–800ms. Standard synchronous HTTP POST endpoints provide no visual feedback during this window, harming user experience in interactive chat interfaces.

## Decision
We added `/api/v1/ws/compress` supporting bidirectional WebSocket streaming:
1. `init`: Payload validation and token accounting.
2. `ranking`: Real-time feedback on BM25 + dense ranking score computation.
3. `summarizing`: Evicted context note generation.
4. `complete`: Full response payload delivery.

## Consequences
- **Positive**: Sub-second perceived latency with progressive visual feedback.
- **Positive**: Standard REST endpoint `/api/v1/compress` remains available for standard backend-to-backend middleware consumption.
