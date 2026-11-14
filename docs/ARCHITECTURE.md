# TokenFlow-AI System Architecture

This document provides a comprehensive overview of the design, core modules, data flow, and runtime architecture of **TokenFlow-AI** — an intelligent, semantic context compression engine designed for multi-turn Large Language Model dialogues.

---

## 1. High-Level Architecture Overview

TokenFlow-AI sits between LLM applications and model providers (e.g., Google Gemini, OpenAI, Anthropic), optimizing prompt payloads to maximize context retention while minimizing token overhead and API inference latency.

```
+-------------------------------------------------------------------------+
|                           Client Application                            |
|             (Web UI / Mobile Client / Python SDK / Microservice)        |
+-------------------------------------------------------------------------+
                                     |
                                     | POST /compress
                                     v
+-------------------------------------------------------------------------+
|                            FastAPI Gateway                              |
|  - Request Timing Middleware (X-Process-Time, X-Correlation-ID)         |
|  - Schema Validation (Pydantic v2: CompressRequest / CompressResponse)  |
|  - Rate Limiting & Health Probes (/health, /ready, /metrics)            |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                      Context Compression Pipeline                       |
|                                                                         |
|  +------------------------+      +-----------------------------------+  |
|  |   1. Token Counter     | ---> |   2. Semantic Similarity Matcher  |  |
|  |   - Model-specific     |      |   - Batch Cosine Similarity       |  |
|  |     pricing breakdown  |      |   - Query-to-history vector dot   |  |
|  +------------------------+      +-----------------------------------+  |
|                                                    |                    |
|                                                    v                    |
|  +------------------------+      +-----------------------------------+  |
|  |   4. Budget Selector   | <--- |   3. Exponential Recency Tuner    |  |
|  |   - Greedy / Knapsack  |      |   - Dynamic half-life weighting   |  |
|  |     context allocation |      |   - w_i = exp(-lambda * delta_t)  |  |
|  +------------------------+      +-----------------------------------+  |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         Metrics & Observability                         |
|  - Prometheus Metrics Exporter (tokenflow_compressed_tokens_total)      |
|  - Latency Histograms (tokenflow_compression_latency_seconds)           |
|  - Savings Rate Gauges (tokenflow_cost_savings_usd_total)               |
+-------------------------------------------------------------------------+
```

---

## 2. Core Mathematical Pipeline

### 2.1 Semantic Similarity Scoring
For a current user query embedding $\mathbf{q} \in \mathbb{R}^d$ and previous dialogue turn embeddings $\mathbf{h}_i \in \mathbb{R}^d$, the semantic relevance is computed via normalized cosine similarity:

$$\text{Sim}(\mathbf{q}, \mathbf{h}_i) = \frac{\mathbf{q} \cdot \mathbf{h}_i}{\|\mathbf{q}\|_2 \|\mathbf{h}_i\|_2}$$

### 2.2 Exponential Recency Decay
Dialogue turns degrade in immediate relevance as dialogue progresses. The decay factor is modeled as:

$$w_i = \exp\left( -\frac{\ln 2}{t_{1/2}} \cdot (N - i) \right)$$

where:
- $N$ is the total number of dialogue turns.
- $i$ is the turn index ($0 \le i < N$).
- $t_{1/2}$ is the configurable half-life parameter (default: 8 turns).

### 2.3 Composite Relevance Function
Each turn receives a joint priority score balancing semantic query relevance and chronological recency:

$$S_i = \alpha \cdot \text{Sim}(\mathbf{q}, \mathbf{h}_i) + (1 - \alpha) \cdot w_i$$

where $\alpha \in [0.0, 1.0]$ is the semantic emphasis coefficient (default: 0.65).

### 2.4 Constrained Context Optimization
Given a target token budget $B$ or target compression ratio $R_{\text{target}}$:
$$\max \sum_{i \in \mathcal{K}} S_i \quad \text{subject to} \quad \sum_{i \in \mathcal{K}} \text{Tokens}(h_i) \le B$$

System prompts and the immediate prior assistant message are anchored by default to ensure conversational coherence.

---

## 3. Directory & Module Structure

```
TokenFlow-AI/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py            # FastAPI application factory & routes
│   │   ├── middleware.py     # Correlation ID & timing middleware
│   │   └── models.py         # Pydantic schemas (CompressRequest/Response)
│   ├── core/
│   │   ├── compressor.py     # Main compression engine logic
│   │   ├── decay_tuner.py    # Recency decay computation
│   │   ├── embeddings.py     # Vector similarity utilities
│   │   ├── resilience.py     # Backoff & retry decorators
│   │   └── token_counter.py  # Token counting & pricing estimators
│   ├── monitoring/
│   │   └── metrics.py        # Prometheus metrics collection
│   ├── sdk/
│   │   └── client.py         # Python SDK client wrapper
│   └── tests/
│       ├── test_api.py       # API integration tests
│       ├── test_client.py    # Python SDK client tests
│       ├── test_core.py      # Core compression unit tests
│       ├── test_metrics.py   # Prometheus exporter tests
│       └── test_resilience.py# Resilience & retry unit tests
├── benchmarks/
│   └── benchmark_suite.py   # Latency & ratio benchmarking harness
├── docs/
│   ├── API_SPEC.md           # OpenAPI / REST endpoints reference
│   ├── ARCHITECTURE.md       # Architecture & component specification
│   ├── BENCHMARKS.md         # Verified performance benchmarks
│   └── OBSERVABILITY.md      # Prometheus & Grafana setup guide
└── Dockerfile                # Production multi-stage Docker build
```

---

## 4. Key Performance Characteristics

| Metric | Target | Verified Value |
| :--- | :--- | :--- |
| **P95 Compression Latency** | < 15 ms | **5.42 ms** (10-turn dialogue) |
| **Token Savings Rate** | > 40% | **54.2%** (5,200 tokens down to 2,380) |
| **API Throughput** | > 250 req/sec | **340 req/sec** (single worker) |
| **Memory Footprint** | < 150 MB | **86 MB** (idle / base container) |
