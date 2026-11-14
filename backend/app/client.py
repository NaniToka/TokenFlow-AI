"""
Lightweight Python SDK client for TokenFlow-AI.
Enables clean, programmatic integration of prompt compression middleware into any LLM application.
"""

from typing import List, Dict, Any, Optional
import requests


class TokenFlowClient:
    """Synchronous client for the TokenFlow AI prompt optimization API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def health(self) -> Dict[str, Any]:
        """Checks liveness status of the TokenFlow server."""
        resp = self.session.get(f"{self.base_url}/api/v1/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def ready(self) -> Dict[str, Any]:
        """Checks readiness status of the TokenFlow server and underlying components."""
        resp = self.session.get(f"{self.base_url}/api/v1/ready", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def compress(
        self,
        history: List[Dict[str, str]],
        current_message: str,
        system_instruction: Optional[str] = "You are a helpful AI assistant.",
        top_k: int = 3,
        alpha: float = 0.7,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compresses dialogue history and packs relevant context into an optimized prompt.
        """
        headers = {"Content-Type": "application/json"}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        payload = {
            "system_instruction": system_instruction,
            "history": history,
            "current_message": current_message,
            "top_k": top_k,
            "alpha": alpha,
        }

        resp = self.session.post(
            f"{self.base_url}/api/v1/compress",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Closes the underlying HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
