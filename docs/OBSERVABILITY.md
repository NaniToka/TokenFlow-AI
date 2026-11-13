# TokenFlow-AI Observability & Metrics Guide

TokenFlow-AI includes real-time telemetry metrics formatted according to the Prometheus open exposition format, accessible directly at `/metrics`.

## Exposed Metrics

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `tokenflow_requests_total` | Counter | Total requests handled, partitioned by `status="success"` and `status="error"` |
| `tokenflow_tokens_original_total` | Counter | Cumulative input tokens before TokenFlow compression |
| `tokenflow_tokens_compressed_total` | Counter | Cumulative input tokens forwarded after compression |
| `tokenflow_tokens_saved_total` | Counter | Cumulative tokens saved across all requests |
| `tokenflow_request_duration_seconds` | Summary | Latency summary distribution (sum and count) |

---

## Prometheus Scrape Configuration
Add TokenFlow-AI as a target in your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "tokenflow-ai"
    metrics_path: "/metrics"
    scrape_interval: 15s
    static_configs:
      - targets: ["tokenflow-backend:8000"]
```

---

## Key PromQL Queries

### 1. Cumulative Token Compression Ratio (%)
```promql
100 * (1 - (rate(tokenflow_tokens_compressed_total[5m]) / rate(tokenflow_tokens_original_total[5m])))
```

### 2. Request Throughput (Requests Per Second)
```promql
sum(rate(tokenflow_requests_total[1m]))
```

### 3. Estimated Cost Savings Per Hour ($ USD)
Assuming Gemini 1.5 Flash input tier ($0.075 / 1M tokens):
```promql
rate(tokenflow_tokens_saved_total[1h]) * 3600 * (0.075 / 1000000)
```
