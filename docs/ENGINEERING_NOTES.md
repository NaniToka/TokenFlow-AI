# Engineering Notes

## What Broke During Development & Fixes

1. **Token Counting Discrepancy**:
   - *Issue*: Initially, the exact token counts from the Gemini API did not match our local approximations, leading to inaccurate savings metrics.
   - *Fix*: Integrated `tiktoken` (`cl100k_base`) to precisely count tokens locally before hitting the LLM API. This unified the measurement and avoided making an extra API call just to check token counts.

2. **Zero-State Fallback Loop**:
   - *Issue*: If the Gemini API key was missing, the application would crash when attempting to fetch embeddings and summaries.
   - *Fix*: Implemented `_local_fallback_summary` (extractive string slicing) and lexical similarity (Jaccard index) when embeddings fail. The application now runs gracefully (albeit with lower compression quality) completely offline.

3. **CORS Conflicts with SPA**:
   - *Issue*: Local frontend React apps were being blocked by CORS when requesting `/api/v1/compress`.
   - *Fix*: Centralized CORS origins via the `.env` configuration (`ALLOWED_ORIGINS`), ensuring both local development (`localhost:5173`) and production domains are whitelisted.

## Cost and Latency Estimates

* **Latency per Request**:
  - **Local Ranking + Fallback Summary**: ~20-50ms (CPU bound by tiktoken and array math).
  - **With Gemini Embedding + Flash Summary**: ~350-500ms (Network bound by Google APIs).
* **Cost Estimates**:
  - `text-embedding-004`: ~$0.00000002 / token.
  - `gemini-1.5-flash` summarization: ~$0.000000075 / token.
  - Overall, the middleware costs ~10x less than the savings it generates by pruning the primary LLM context window. Assuming 500 input tokens saved per turn at $0.001 / 1K tokens, TokenFlow saves ~$0.0005 per turn, costing only ~$0.00005 to run.

## Scaling to 100x Traffic

If traffic spikes to 100x, the current architecture would hit bottlenecks. To adapt:

1. **Async Summarization & Batching**: The current `process_compression` synchronously blocks while waiting for Gemini to summarize turns. At 100x scale, this will exhaust Uvicorn worker threads. We would move summarization to an async job queue (e.g., Celery + Redis).
2. **Caching Embeddings**: Currently, every request re-embeds the entire chat history. At 100x scale, we'd hash the turn contents and store their 768-dim vectors in Redis or Pinecone. We only embed the *new* query.
3. **Horizontal Scaling**: Fastapi is stateless, so we can spin up multiple containers behind an AWS ALB or Google Cloud Run load balancer. Rate limiting needs to move from in-memory SlowAPI to a shared Redis cluster to prevent abuse across instances.
4. **gRPC instead of REST**: To minimize parsing overhead on massive chat arrays, transitioning the internal middleware communication from JSON/REST to Protobufs/gRPC would significantly cut deserialization CPU usage.
