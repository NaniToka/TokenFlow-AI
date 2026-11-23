import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import CompressRequest, Turn

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "features" in data


def test_compress_endpoint_success():
    payload = {
        "system_instruction": "You are a test bot.",
        "history": [
            {"role": "user", "content": "Hi there"},
            {"role": "model", "content": "Hello!"}
        ],
        "current_message": "How are you?",
        "top_k": 1,
        "recency_weight": 0.5
    }
    response = client.post("/api/v1/compress", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "final_prompt" in data
    assert "tokens_saved" in data
    assert "metadata" in data


def test_compress_endpoint_empty_current_message():
    payload = {
        "history": [],
        "current_message": ""
    }
    response = client.post("/api/v1/compress", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_compress_endpoint_huge_input():
    payload = {
        "history": [
            {"role": "user", "content": "word " * 1000}
        ],
        "current_message": "test",
        "top_k": 1
    }
    response = client.post("/api/v1/compress", json=payload)
    assert response.status_code == 200
    assert response.json()["compressed_tokens"] > 0


def test_batch_compress_endpoint():
    payload = {
        "requests": [
            {
                "history": [{"role": "user", "content": "Query 1 background"}],
                "current_message": "Query 1 message",
                "top_k": 1,
            },
            {
                "history": [{"role": "user", "content": "Query 2 background"}],
                "current_message": "Query 2 message",
                "top_k": 1,
            }
        ]
    }
    response = client.post("/api/v1/compress/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert "total_tokens_saved" in data


def test_stats_lifecycle():
    # Fetch stats
    res1 = client.get("/api/v1/stats")
    assert res1.status_code == 200
    assert "total_requests" in res1.json()

    # Reset stats
    res2 = client.post("/api/v1/stats/reset")
    assert res2.status_code == 200
    assert res2.json()["status"] == "success"

    # Verify reset
    res3 = client.get("/api/v1/stats")
    assert res3.json()["total_requests"] == 0


def test_websocket_compress_stream():
    with client.websocket_connect("/api/v1/ws/compress") as ws:
        payload = {
            "history": [{"role": "user", "content": "WS history turn"}],
            "current_message": "WS current query",
            "top_k": 1
        }
        ws.send_json(payload)
        msg1 = ws.receive_json()
        assert msg1["stage"] == "init"
        msg2 = ws.receive_json()
        assert msg2["stage"] == "ranking"
        msg3 = ws.receive_json()
        assert msg3["stage"] == "summarizing"
        msg4 = ws.receive_json()
        assert msg4["stage"] == "complete"
        assert "final_prompt" in msg4["result"]
