import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import CompressRequest, Turn

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

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
