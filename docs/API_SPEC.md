# TokenFlow-AI REST API Specification

TokenFlow-AI exposes an in-memory middleware REST API engineered to optimize conversation history before forwarding to Large Language Models.

## Base URL
```
http://localhost:8000
```

---

## 1. Health & Readiness Probes

### `GET /api/v1/health`
Liveness probe checking container responsiveness.

- **Status Code**: `200 OK`
- **Response**:
```json
{
  "status": "healthy",
  "service": "TokenFlow AI",
  "version": "1.0.0"
}
```

### `GET /api/v1/ready`
Readiness probe verifying underlying tokenizer dependencies and memory buffers.

- **Status Code**: `200 OK`
- **Response**:
```json
{
  "status": "ready",
  "service": "TokenFlow AI",
  "checks": {
    "tokenizer": "ok",
    "in_memory_pipeline": "ready"
  }
}
```

---

## 2. Prompt Compression Endpoint

### `POST /api/v1/compress`
Compresses conversation history turns and packs the highest-relevance context with an extractive memory summary.

#### Request Headers
| Header | Type | Description |
| :--- | :--- | :--- |
| `Content-Type` | `string` | Must be `application/json` |
| `X-Correlation-ID` | `string` | *(Optional)* Client-supplied UUID for end-to-end distributed tracing. Auto-generated if omitted. |

#### Request Body
```json
{
  "system_instruction": "You are a customer service assistant.",
  "history": [
    {"role": "user", "content": "How do I upgrade my billing tier?"},
    {"role": "model", "content": "Navigate to Settings > Billing and select Pro."}
  ],
  "current_message": "Where is the invoice history located?",
  "top_k": 3,
  "alpha": 0.7
}
```

#### Response Headers
| Header | Description |
| :--- | :--- |
| `X-Correlation-ID` | Echoed correlation tracking ID |
| `X-Process-Time-Ms` | Server execution duration in milliseconds (typically < 2.0 ms) |

#### Response Body (`200 OK`)
```json
{
  "summary": "User inquired about billing tier upgrade to Pro.",
  "selected_turns": [
    {"role": "user", "content": "How do I upgrade my billing tier?"}
  ],
  "final_prompt": "Prior context summary:\n• User inquired about billing tier upgrade...\n\nUser: Where is the invoice history located?",
  "original_tokens": 128,
  "compressed_tokens": 64,
  "tokens_saved": 64,
  "cost_before_usd": 0.0000096,
  "cost_after_usd": 0.0000048,
  "cost_saved_usd": 0.0000048,
  "compression_ratio": 50.0
}
```

---

## Error Handling
- **`400 Bad Request`**: Malformed request content.
- **`422 Unprocessable Entity`**: Schema validation failed (`top_k` out of bounds, blank content, or unsupported role).
- **`429 Too Many Requests`**: Rate limit exceeded (configurable via `RATE_LIMIT_PER_MINUTE`).
- **`503 Service Unavailable`**: Core tokenizer initialization failed.
