import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.cache.semantic_cache import summary_cache

client = TestClient(app)


def test_models_and_compression_modes():
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert len(data["models"]) >= 6
    assert any(m["id"] == "claude-3-5-sonnet" for m in data["models"])
    assert len(data["compression_modes"]) == 4


def test_rag_workbench_endpoints():
    client.delete("/api/v1/rag/clear")

    doc_text = (
        "TokenFlow AI uses Okapi BM25 combined with Gemini 768-dimensional embeddings.\n\n"
        "PgBouncer manages PostgreSQL database connection pooling efficiently.\n\n"
        "Redis LRU caching skips duplicate summarization requests."
    )
    idx_res = client.post("/api/v1/rag/index", json={
        "text": doc_text,
        "chunk_size": 120,
        "chunk_overlap": 20,
        "source_name": "architecture.md",
    })
    assert idx_res.status_code == 200
    idx_data = idx_res.json()
    assert idx_data["chunks_indexed"] >= 2
    assert idx_data["total_store_chunks"] == idx_data["chunks_indexed"]

    q_res = client.post("/api/v1/rag/query", json={
        "query": "How does PgBouncer manage database connections?",
        "top_k": 2,
        "alpha": 0.5,
    })
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert len(q_data["results"]) >= 1
    assert "PgBouncer" in q_data["results"][0]["text"]

    clr_res = client.delete("/api/v1/rag/clear")
    assert clr_res.status_code == 200
    assert clr_res.json()["total_indexed"] == 0


def test_pii_redaction_and_sanitize_endpoint():
    raw = "Connect using sk-1234567890abcdef1234567890abcdef and email admin@acme.org from 192.168.1.10 <script>alert(1)</script>"
    res = client.post("/api/v1/sanitize", json={"text": raw, "redact_pii": True})
    assert res.status_code == 200
    data = res.json()
    assert data["xss_stripped"] == 1
    assert data["redactions_count"] == 3
    assert "OPENAI_KEY" in data["redacted_types"]
    assert "EMAIL" in data["redacted_types"]
    assert "IPV4_ADDR" in data["redacted_types"]
    assert "admin@acme.org" not in data["sanitized_text"]
    assert "[REDACTED_EMAIL]" in data["sanitized_text"]

    # Also test end-to-end inside /compress
    comp_res = client.post("/api/v1/compress", json={
        "history": [
            {"role": "user", "content": "My key is AIzaSyD123456789012345678901234567890"},
            {"role": "model", "content": "Got it, stored safely."},
            {"role": "user", "content": "Send alerts to ops@example.com"},
            {"role": "model", "content": "Configured email alerting."},
        ],
        "current_message": "Rotate credentials now",
        "top_k": 2,
        "sanitize_pii": True,
        "target_model": "gpt-4o",
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["metadata"]["redaction"]["enabled"] is True
    assert comp_data["metadata"]["redaction"]["redactions_count"] >= 2
    assert "ops@example.com" not in comp_data["final_prompt"]


def test_rank_inspect_and_evaluate_endpoints():
    history = [
        {"role": "user", "content": "We are deploying FastAPI on Kubernetes EKS."},
        {"role": "model", "content": "Configure liveness probes and horizontal pod autoscaler."},
        {"role": "user", "content": "What is the weather in Tokyo?"},
        {"role": "model", "content": "It is sunny and 22C in Tokyo today."},
        {"role": "user", "content": "```python\ndef handler():\n    raise ConnectionError('db timeout')\n```"},
        {"role": "model", "content": "Wrap the connection call with exponential backoff retries."},
    ]
    inspect_res = client.post("/api/v1/rank/inspect", json={
        "history": history,
        "current_message": "Fix ConnectionError db timeout in handler",
        "top_k": 2,
        "compression_mode": "code_preserving",
    })
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    assert len(inspect_data["scores"]) == 6
    assert inspect_data["drift_detected"] is True

    # Run compression & then evaluate
    comp_res = client.post("/api/v1/compress", json={
        "history": history,
        "current_message": "Fix ConnectionError db timeout in handler",
        "top_k": 2,
        "compression_mode": "code_preserving",
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    eval_res = client.post("/api/v1/evaluate", json={
        "history": history,
        "response": comp_data,
    })
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "composite_grade" in eval_data
    assert eval_data["lexical_recall"] >= 0.0


def test_semantic_cache_hit_and_telemetry():
    client.post("/api/v1/cache/clear")
    payload = {
        "history": [
            {"role": "user", "content": "Turn one discusses PostgreSQL B-Tree indexes and vacuuming."},
            {"role": "model", "content": "Turn two explains autovacuum thresholds and fillfactor."},
            {"role": "user", "content": "Turn three discusses Redis eviction policies like allkeys-lru."},
            {"role": "model", "content": "Turn four explains memory fragmentation ratio."},
            {"role": "user", "content": "Turn five asks about Docker multi-stage builds."},
            {"role": "model", "content": "Turn six recommends slim base images."},
        ],
        "current_message": "How should I tune autovacuum in Postgres?",
        "top_k": 2,
        "use_cache": True,
    }
    r1 = client.post("/api/v1/compress", json=payload)
    assert r1.status_code == 200
    assert r1.json()["metadata"]["cache_hit"] is False

    r2 = client.post("/api/v1/compress", json=payload)
    assert r2.status_code == 200
    assert r2.json()["metadata"]["cache_hit"] is True

    c_stats = client.get("/api/v1/cache/stats").json()
    assert c_stats["summary_cache"]["hits"] >= 1

    tel_res = client.get("/api/v1/telemetry")
    assert tel_res.status_code == 200
    tel_data = tel_res.json()
    assert "percentiles" in tel_data["latency"]
    assert "p95" in tel_data["latency"]["percentiles"]


def test_async_compress_and_export_formats():
    async_res = client.post("/api/v1/compress/async", json={
        "history": [
            {"role": "user", "content": "Explain consistent hashing in distributed caches."},
            {"role": "model", "content": "Consistent hashing maps keys onto a unit ring with virtual nodes."},
        ],
        "current_message": "Why use virtual nodes?",
        "top_k": 1,
    })
    assert async_res.status_code == 200
    task_id = async_res.json()["task_id"]

    status_res = client.get(f"/api/v1/tasks/{task_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in {"PENDING", "PROCESSING", "COMPLETED"}

    # Test export formats
    comp_res = client.post("/api/v1/compress", json={
        "history": [
            {"role": "user", "content": "Turn 1 context"},
            {"role": "model", "content": "Turn 2 context"},
            {"role": "user", "content": "Turn 3 context"},
            {"role": "model", "content": "Turn 4 context"},
        ],
        "current_message": "Final question",
        "top_k": 1,
    }).json()

    md_res = client.post("/api/v1/export/markdown", json=comp_res)
    assert md_res.status_code == 200
    assert "TokenFlow AI" in md_res.text

    csv_res = client.post("/api/v1/export/csv", json=comp_res)
    assert csv_res.status_code == 200
    assert "BM25 Score" in csv_res.text

    json_res = client.post("/api/v1/export/json", json=comp_res)
    assert json_res.status_code == 200
    assert "final_prompt" in json_res.text
