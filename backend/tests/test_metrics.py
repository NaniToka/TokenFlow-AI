import pytest
from app.utils.metrics import MetricsRegistry


def test_metrics_registry_initial_state():
    registry = MetricsRegistry()
    output = registry.generate_prometheus_output()
    assert 'tokenflow_requests_total{status="success"} 0' in output
    assert "tokenflow_tokens_saved_total 0" in output


def test_metrics_registry_record_success():
    registry = MetricsRegistry()
    registry.record_request(original_tokens=100, compressed_tokens=40, duration_seconds=0.015, success=True)

    output = registry.generate_prometheus_output()
    assert 'tokenflow_requests_total{status="success"} 1' in output
    assert "tokenflow_tokens_original_total 100" in output
    assert "tokenflow_tokens_compressed_total 40" in output
    assert "tokenflow_tokens_saved_total 60" in output
    assert "tokenflow_request_duration_seconds_count 1" in output


def test_metrics_registry_record_error():
    registry = MetricsRegistry()
    registry.record_request(original_tokens=0, compressed_tokens=0, duration_seconds=0.005, success=False)

    output = registry.generate_prometheus_output()
    assert 'tokenflow_requests_total{status="error"} 1' in output
    assert 'tokenflow_requests_total{status="success"} 0' in output


def test_metrics_endpoint_via_client():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "tokenflow_requests_total" in response.text
