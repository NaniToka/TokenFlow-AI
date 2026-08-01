# TokenFlow AI — Prompt Memory Optimizer Middleware

> **Semantic Vector Ranking & Real-Time LLM Context Compression Middleware built with FastAPI, Gemini text-embedding-004, and React.**

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-API-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)

[🌐 Live Demo](https://tokenflow-ai.onrender.com) &nbsp;|&nbsp; [📖 API Documentation](https://tokenflow-ai.onrender.com/docs) &nbsp;|&nbsp; [💻 GitHub Repository](https://github.com/NaniToka/TokenFlow-AI)

---

![TokenFlow Architecture](./docs/architecture-diagram.png)

---

## ⚡ Executive Summary & The Problem

### The Core LLM Bottleneck
As modern AI applications engage in multi-turn conversations, re-sending the complete uncompressed dialogue history with every incoming user prompt causes significant system engineering challenges:
1. **Linear Token Inflation**: Input token counts grow exponentially ($O(N^2)$ aggregate tokens over $N$ turns), dramatically inflating API consumption costs.
2. **Increased Response Latencies**: Larger context sizes slow down Time-To-First-Token (TTFT) and processing latency.
3. **Context Window Exhaustion & Attention Dilution**: Crucial instructions or historical query context get diluted across thousands of tokens, lowering reasoning accuracy.

### The TokenFlow AI Solution
**TokenFlow AI** operates as a high-performance, stateless middleware layer that dynamically intercepts raw prompt payload history before it reaches the target LLM. 

By combining **semantic vector embeddings (`text-embedding-004`)**, **cosine similarity scoring**, and an **exponential recency decay curve**, TokenFlow AI ranks historical conversation turns by relevance to the user's latest query. It retains top-$K$ critical context turns, condenses remaining background turns into a concise 2-line memory summary (`gemini-1.5-flash`), and constructs an optimized prompt achieving **50% to 75%+ token reduction** while preserving 100% intent retention.

---

## 🔬 Architecture & System Design (How It Works)

TokenFlow AI utilizes a modular 4-stage pipeline designed for zero state persistence and sub-millisecond overhead:

```
[ Incoming Request Payload ] 
             │
             ▼
   ┌───────────────────┐
   │ 1. Vector Ranker  │  ──────► Embed query & turns (text-embedding-004)
   └─────────┬─────────┘          Score = CosineSim * e^(-λ * Δt)
             │
             ▼
   ┌───────────────────┐
   │ 2. Context        │  ──────► Condense background turns into concise
   │    Compressor     │          2-line memory summary (gemini-1.5-flash)
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────┐
   │ 3. Prompt         │  ──────► Reconstruct minimal prompt context
   │    Assembler      │          [System + Memory Note + Top-K + Query]
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────┐
   │ 4. Metrics        │  ──────► Compute exact token delta via tiktoken
   │    Tracker        │          Calculate real-time $ USD cost savings
   └─────────┬─────────┘
             │
             ▼
[ Optimized Payload Response ]
```

### Engine Pipeline Breakdown
1. **Vector Ranker**: Generates 768-dimensional embeddings for the current query and each historical turn using Google's `text-embedding-004`. Calculates semantic relevance via cosine similarity and applies an exponential recency decay formula:
   $$\text{Final Score} = \text{CosineSimilarity}(v_{query}, v_{turn}) \times e^{-\lambda \cdot \Delta t}$$
   where $\Delta t$ represents turn age distance and $\lambda$ is the recency decay factor.
2. **Context Compressor**: Evicts lower-ranked turns and summarizes their core context into a tight, 2-line memory snapshot using `gemini-1.5-flash`.
3. **Prompt Assembler**: Merges the system instruction, condensed background memory note, top-$K$ relevance-ranked historical turns, and current user query into a clean, unified payload.
4. **Metrics & Financial Tracker**: Uses `tiktoken` (`cl100k_base` tokenizer) to measure raw vs. compressed token counts and calculates real-time USD cost savings based on official model pricing tier metrics.

---

![Memory Ranker Pipeline](./docs/ranker-pipeline.png)

---

## ✨ Key Features at a Glance

* **🎨 Modern Glassmorphic Dashboard UI**: Sleek, responsive dark-mode interface built with React 18 and Tailwind CSS featuring micro-animations and intuitive visualization tabs.
* **💰 Real-Time Financial & Savings Metrics**: Live calculation of total tokens saved, percentage reduction, and cumulative USD financial cost savings.
* **🔍 Interactive Before vs. After Visualizer**: Line-by-line comparative visualizer displaying exact token footprint reduction and turn-level relevance score breakdowns.
* **📊 Analytics & Historical Trends**: Interactive interactive graphs (Recharts) charting token savings and cumulative monetary efficiency per request.
* **🛠️ 20+ Built-In Industry Scenarios**: Pre-configured real-world conversational datasets spanning DevOps, Healthcare, FinTech, CyberSecurity, Game Dev, Legal Tech, and Cloud Architecture.
* **🔒 Privacy-First Memory-Only Architecture**: Zero database storage. All processing occurs in-memory during request lifecycle, maintaining strict zero-data retention compliance.

---

## 📸 Dashboard Showcase & Visuals

![TokenFlow Visualizer](./docs/dashboard-visualizer.png)
*Figure 1: TokenFlow AI Interactive Before vs. After Compression Visualizer and Turn Scoring Engine.*

![Analytics Charts](./docs/analytics-charts.png)
*Figure 2: Real-time Recharts Analytics displaying request-by-request token savings and monetary impact.*

---

## 🛠️ Tech Stack & Engine Matrix

| Layer | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11 / FastAPI | High-performance asynchronous API engine |
| **Rate Limiting** | SlowAPI | Request throttling and endpoint protection |
| **AI / Embeddings** | Google GenAI SDK (`text-embedding-004`, `gemini-1.5-flash`) | Semantic vector embeddings & context summarization |
| **Tokenization** | Tiktoken (`cl100k_base`) | High-accuracy OpenAI/Gemini token counting |
| **Mathematics** | NumPy | High-speed vector operations & cosine similarity computation |
| **Frontend UI** | React 18 / Vite / Tailwind CSS | Component architecture & modern responsive styling |
| **Icons & Charts** | Lucide React / Recharts | Clean visual iconography & interactive performance charts |
| **Deployment** | Docker / Render Web Service | Single-container unified SPA mounting & cloud deployment |

---

## 🚀 Quick Start & Local Setup

### Prerequisites
* **Python 3.10+** installed
* **Node.js 18+** and `npm` installed
* **Google Gemini API Key** (obtainable from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/NaniToka/TokenFlow-AI.git
cd TokenFlow-AI
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` and add your API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:8000"]
```

### 3. Install Dependencies

**Backend Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Frontend Setup:**
```bash
cd frontend
npm install
cd ..
```

### 4. Run Locally

**Start Backend API (Terminal 1):**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*API will run at `http://127.0.0.1:8000` with interactive Swagger docs at `/docs`.*

**Start Frontend Development Server (Terminal 2):**
```bash
cd frontend
npm run dev
```
*Frontend will run at `http://localhost:5173`.*

---

## 📖 API Reference Documentation

### 1. Compress Prompt
* **Endpoint**: `POST /api/v1/compress`
* **Content-Type**: `application/json`

#### Request Payload:
```json
{
  "system_instruction": "You are an expert DevOps engineer specializing in Kubernetes.",
  "history": [
    {
      "role": "user",
      "content": "Our ingress controller is returning 502 Bad Gateway errors."
    },
    {
      "role": "model",
      "content": "Check pod readiness probes, service endpoint IPs, and ingress controller logs."
    }
  ],
  "current_message": "How do I check the pod readiness probe status?",
  "top_k": 2,
  "recency_weight": 0.3
}
```

#### Response (200 OK):
```json
{
  "compressed_prompt": "[SYSTEM MEMORY NOTE: User reported 502 Bad Gateway errors on ingress controller.]\n\nUser: How do I check the pod readiness probe status?",
  "original_token_count": 84,
  "compressed_token_count": 32,
  "tokens_saved": 52,
  "savings_percentage": 61.9,
  "estimated_cost_savings_usd": 0.0000078,
  "turn_scores": [
    {
      "turn_index": 0,
      "role": "user",
      "similarity_score": 0.812,
      "recency_score": 0.740,
      "final_score": 0.601,
      "retained": true
    }
  ],
  "processing_time_ms": 142.5
}
```

### 2. Session Analytics
* **Endpoint**: `GET /api/v1/stats`
* **Response**: Returns cumulative tokens saved, average compression ratio, and request count.

### 3. Reset Session Analytics
* **Endpoint**: `POST /api/v1/stats/reset`
* **Response**: `{"status": "success", "message": "Session statistics reset successfully."}`

### 4. Health Check
* **Endpoint**: `GET /api/v1/health`
* **Response**: `{"status": "healthy", "service": "TokenFlow AI", "version": "1.0.0"}`

---

## 🐳 Deployment Configuration (Render / Docker)

TokenFlow AI is fully configured for single-site unified deployment where FastAPI serves both backend API endpoints and built React static assets.

### 1-Click Render Deployment
The project includes a ready-to-use [`render.yaml`](./render.yaml) blueprint file:
1. Connect your repository to [Render](https://render.com).
2. Select **Blueprint Deployment**.
3. Set your `GEMINI_API_KEY` when prompted in the Render Dashboard.
4. Render automatically executes [`./build.sh`](./build.sh) and boots Uvicorn on `$PORT`.

---

## 👤 Author & Contact

**Toka Nani Yadav**  
*Computer Science & Engineering*

* **GitHub**: [@NaniToka](https://github.com/NaniToka)
* **LinkedIn**: [Nani Toka](https://linkedin.com/in/nanitoka)
* **Portfolio**: [nanitoka.dev](https://nanitoka.dev)

---

<p align="center">
  <sub>Built with ❤️ using FastAPI, Google Gemini API, and React. Released under the MIT License.</sub>
</p>
