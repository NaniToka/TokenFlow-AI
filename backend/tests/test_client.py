import pytest
from unittest.mock import patch, MagicMock
from app.client import TokenFlowClient


def test_client_init_and_close():
    client = TokenFlowClient(base_url="http://testserver:8000")
    assert client.base_url == "http://testserver:8000"
    client.close()


def test_client_context_manager():
    with TokenFlowClient(base_url="http://testserver:8000") as client:
        assert client.base_url == "http://testserver:8000"


@patch("requests.Session.get")
def test_client_health(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "healthy", "service": "TokenFlow AI"}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    with TokenFlowClient() as client:
        health = client.health()
        assert health["status"] == "healthy"
        mock_get.assert_called_once_with("http://localhost:8000/api/v1/health", timeout=10.0)


@patch("requests.Session.post")
def test_client_compress(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "final_prompt": "compressed prompt",
        "tokens_saved": 42,
        "compression_ratio": 45.0,
    }
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    with TokenFlowClient() as client:
        res = client.compress(
            history=[{"role": "user", "content": "hello"}],
            current_message="world",
            correlation_id="trace-1234",
        )
        assert res["tokens_saved"] == 42
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-Correlation-ID"] == "trace-1234"
