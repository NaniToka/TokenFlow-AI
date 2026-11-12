import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import CompressRequest, Turn

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_probe():
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["tokenizer"] == "ok"


def test_correlation_and_process_time_headers():
    custom_id = "test-correlation-abc-123"
    response = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_id
    assert "X-Process-Time-Ms" in response.headers
    # When no correlation ID is provided, an auto-generated one should be returned
    response_auto = client.get("/health")
    assert response_auto.headers.get("X-Correlation-ID") is not None


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

def test_compress_endpoint_empty_current_message():
    payload = {
        "history": [],
        "current_message": ""
    }
    response = client.post("/api/v1/compress", json=payload)
    # FastAPI returns 422 Unprocessable Entity on schema validation failure
    assert response.status_code in (400, 422)

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


def test_compress_endpoint_invalid_role():
    payload = {
        "history": [
            {"role": "unsupported_role", "content": "hello"}
        ],
        "current_message": "test",
    }
    response = client.post("/api/v1/compress", json=payload)
    assert response.status_code == 422


def test_compress_endpoint_role_normalization():
    payload = {
        "history": [
            {"role": "USER", "content": "hello from uppercase user"},
            {"role": "Model", "content": "hello from titlecase model"}
        ],
        "current_message": "test",
    }
    response = client.post("/api/v1/compress", json=payload)
    assert response.status_code == 200


def test_compress_endpoint_top_k_bounds():
    # top_k must be between 1 and 20
    payload_too_high = {
        "history": [],
        "current_message": "test",
        "top_k": 25,
    }
    res_high = client.post("/api/v1/compress", json=payload_too_high)
    assert res_high.status_code == 422

    payload_zero = {
        "history": [],
        "current_message": "test",
        "top_k": 0,
    }
    res_zero = client.post("/api/v1/compress", json=payload_zero)
    assert res_zero.status_code == 422

