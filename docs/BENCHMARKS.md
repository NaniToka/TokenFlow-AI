# TokenFlow-AI Verified Performance Benchmarks

This report documents reproducible latency, token reduction, and cloud API cost savings measured across multi-turn conversational workloads using TokenFlow-AI's hybrid semantic and recency compressor.

## Summary Results

| Conversation Turns | Original Tokens | Compressed Tokens | Reduction % | P50 Latency (ms) | P90 Latency (ms) | Gemini Cost Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **10 Turns** | 206 | 126 | **38.83%** | 0.23 ms | 0.39 ms | ~39% Saved |
| **25 Turns** | 474 | 125 | **73.63%** | 0.41 ms | 0.45 ms | ~74% Saved |
| **50 Turns** | 982 | 130 | **86.76%** | 0.78 ms | 0.82 ms | ~87% Saved |
| **100 Turns** | 1,952 | 130 | **93.34%** | 1.50 ms | 1.63 ms | ~93% Saved |

## Methodology
- **Hardware**: Apple Silicon (arm64), Python 3.12, FastAPI backend.
- **Scoring**: Hybrid alpha-weighted ranking ($\alpha = 0.7$ semantic similarity, $0.3$ exponential recency decay).
- **Token Encoding**: OpenAI `cl100k_base` via `tiktoken`.
- **Cost Model**: Standard Google Gemini 1.5 Flash input tier ($0.075 per 1,000,000 tokens).

## Reproducibility
Run the benchmark directly from the repository root:
```bash
python benchmarks/compression_benchmark.py
```
All numbers above reflect the statistical median over 20 iterations per dialogue tier.
