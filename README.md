# TokenFlow AI

> **A high-performance, stateless intelligent context middleware and prompt memory optimizer that eliminates quadratic context window bloat in LLM applications.**

[![CI](https://github.com/NaniToka/TokenFlow-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/NaniToka/TokenFlow-AI/actions)
[![Coverage](https://img.shields.io/badge/Coverage-94%25-brightgreen.svg)](#)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini%20API-4285F4?logo=googlegemini&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

---

## ⚡ The Problem
Modern conversational AI workflows suffer from a compounding systems challenge: **re-transmitting full uncompressed chat histories on every turn scales input tokens quadratically ($O(N^2)$)**.

This introduces three critical failure modes in production:
1. **Exponential API Cost Inflation**: Redundant conversational filler consumes expensive LLM input quota.
2. **Degraded Time-To-First-Token (TTFT)**: Massive prompt payloads increase pre-fill latency on transformer models.
3. **Context Window Exhaustion & Attention Diffusion**: Distant, irrelevant turns dilute model attention away from immediate operational constraints.

---

## 💡 The Solution: TokenFlow AI
TokenFlow AI sits as an ultra-low-latency middleware proxy between client applications and downstream LLM APIs (Google Gemini, OpenAI, Anthropic). It continuously prunes conversational history into an optimal token representation through a **multi-strategy ranking engine** and **abstractive memory summarization**.

```mermaid
graph TD
    Client([Client App / Frontend]) -->|HTTP / WebSocket| Gateway[FastAPI Ingress Gateway]
    Gateway --> Tracing[Correlation ID & Latency Tracing]
    Tracing --> Pipeline[Compression Pipeline]

    subgraph "Intelligent Multi-Strategy Ranking Engine"
        Pipeline --> BM25[Okapi BM25 Sparse Scorer]
        Pipeline --> Dense[Dense Vector Embeddings (Gemini 768-d)]
        Pipeline --> Drift[Conversational Drift Detector]
        Pipeline --> Decay[Exponential Recency Weighting]
        BM25 & Dense & Drift & Decay --> Ranker[Adaptive Alpha Tuner]
    end

    Ranker -->|Top-K Selected Turns| Assembler[Prompt Assembler]
    Ranker -->|Evicted Context Turns| Summarizer[Abstractive Context Summarizer]

    Summarizer -->|Compact 2-3 Line Note| Assembler
    Assembler --> Cache[(Semantic LRU Cache)]
    Assembler --> Response([Optimized Prompt Payload])
```

---

## 📊 Benchmark Results

Evaluated across synthetic multi-turn technical dialogues comparing uncompressed conversation history against TokenFlow AI compressed output:

| Metric | Baseline | TokenFlow AI | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Token Reduction** | 574 tokens | **368 tokens** | **-35.89%** |
| **Input Cost (Gemini Flash)** | \$0.000043 | **\$0.000028** | **-35.89%** |
| **Semantic Fidelity Score** | 100% | **96.41%** | **High Retention (Grade A)** |
| **Lexical Fact Recall** | 100% | **94.8%** | **Near Lossless** |
| **Middleware Latency (Local)** | 0ms | **~4.2ms** | Sub-millisecond CPU overhead |

> Reproduce benchmark numbers locally via `python benchmarks/run.py`.

---

## 🛠️ Key Architectural Decisions

Detailed Architecture Decision Records (ADRs) document the engineering trade-offs:

1. **[ADR-001: Hybrid BM25 & Dense Vector Ranking Engine](docs/adr/001-hybrid-bm25-dense-ranking.md)**
   * *Rationale*: Pure semantic similarity misses exact IDs, flags, and error codes. Combining BM25 with dense vectors guarantees exact identifier preservation while maintaining semantic nuance.
2. **[ADR-002: 100% Stateless Memory Design](docs/adr/002-stateless-memory-architecture.md)**
   * *Rationale*: Eliminates GDPR and HIPAA compliance risks by strictly executing in-memory without persistent database storage of prompt contents.
3. **[ADR-003: Real-Time WebSocket Streaming](docs/adr/003-websocket-streaming-protocol.md)**
   * *Rationale*: Provides sub-second progressive status updates (`init` → `ranking` → `summarizing` → `complete`) for interactive UIs.
4. **[ADR-004: Resilient Offline-Calibrated Tokenization](docs/adr/004-offline-calibrated-tokenization.md)**
   * *Rationale*: Dual-mode token accounting falls back to calibrated subword heuristic when external BPE files cannot be downloaded in air-gapped VPCs.
5. **[ADR-005: RRF Fusion, MMR Diversity & N-Gram Reranking](docs/adr/005-rrf-mmr-reranking-pipeline.md)**
   * *Rationale*: Scale-invariant rank fusion and diversity sampling eliminate redundant retry turns without extra model dependencies.
6. **[ADR-006: Hard Knapsack Token Budgeting & Hierarchical Summarization](docs/adr/006-knapsack-token-budgeting.md)**
   * *Rationale*: Guarantees downstream context-window SLAs while preventing middle-context amnesia on 12+ evicted turns.
7. **[ADR-007: Prompt Injection Firewall & LLM Circuit Breaker](docs/adr/007-prompt-injection-firewall-and-circuit-breaker.md)**
   * *Rationale*: Deterministic `INJ-001..005` threat scanning and 3-state circuit breaking ensure zero-trust reliability during upstream outages.

---

## 🚀 Quickstart

### Option A: Docker Compose (Recommended)
```bash
git clone https://github.com/NaniToka/TokenFlow-AI.git
cd TokenFlow-AI
cp backend/.env.example backend/.env
docker compose up -d
curl http://localhost:8000/api/v1/health
```

### Option B: Local Development
```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup (in a separate terminal)
cd ../frontend
npm install
npm run dev
```

Visit the interactive dashboard at **`http://localhost:8000`** (or `http://localhost:5173` in development).

---

## 🧪 Verification & Testing

The repository maintains strict test coverage enforced through automated CI workflows:

```bash
# Run complete test suite (53 unit & integration tests)
PYTHONPATH=backend pytest backend/tests -v

# Run with coverage report
PYTHONPATH=backend pytest backend/tests --cov=backend/app --cov-report=term-missing

# Run benchmark reproduction script
python benchmarks/run.py
```

---

## 📡 API Reference

### 1. Optimize Prompt (`POST /api/v1/compress`)
Compresses a conversation history into an optimal token prompt.

```bash
curl -X POST http://localhost:8000/api/v1/compress \
  -H "Content-Type: application/json" \
  -d '{
    "history": [
      {"role": "user", "content": "We are setting up AWS EKS with Terraform."},
      {"role": "model", "content": "Make sure your DynamoDB table has LockID as the primary key."}
    ],
    "current_message": "How do I fix the DynamoDB state lock conflict?",
    "top_k": 1
  }'
```

### 2. Drop-In OpenAI Chat Compressor (`POST /api/v1/chat/compress`)
Directly accepts OpenAI `messages: [{role, content}]` arrays, optimizes context, and returns a compressed message array.

### 3. Batch & Streaming Channels (`POST /api/v1/compress/batch`, `POST /api/v1/compress/stream`, `WS /api/v1/ws/compress`)
Concurrent batch optimization plus Server-Sent Events (SSE) and WebSocket real-time progress streaming.

### 4. HyDE RAG Ingestion & Grounded Citations (`POST /api/v1/rag/upload`, `POST /api/v1/rag/query`)
Ingests `.md/.py/.txt/.json/.csv/.log` files, expands queries via HyDE synonyms, applies N-gram reranking, and attaches `[Chunk #i]` citations.

### 5. Evaluation, Security Firewall & Observability
- `POST /api/v1/evaluate/needle`: Needle-in-a-Haystack context retention stress test
- `POST /api/v1/experiments/compare`: Side-by-side Variant A vs B strategy benchmarking
- `POST /api/v1/guard/scan`: Zero-trust prompt injection firewall (`INJ-001..005`) + PII/XSS redactor
- `GET /api/v1/logs`, `GET /api/v1/circuit-breaker`, `GET /api/v1/sdk-snippets`, `GET /api/v1/stats`: Live trace ring buffer, circuit breaker, multi-language SDK codegen, and telemetry.

---

## 🗺️ Engineering Documentation
- [System Design Document](docs/SYSTEM_DESIGN.md)
- [Architecture Decision Records (ADR)](docs/adr/README.md)
- [Engineering Notes (Cost & Latency)](docs/ENGINEERING_NOTES.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
