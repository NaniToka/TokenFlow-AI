"""
Multi-Language SDK Snippet Code Generator.

Generates copy-ready client code for Python httpx, TypeScript fetch,
OpenAI drop-in chat wrapper, and cURL based on active pipeline parameters.
"""

from __future__ import annotations


def generate_sdk_snippets(
    base_url: str = "http://localhost:8000",
    target_model: str = "gemini-1.5-flash",
    compression_mode: str = "balanced",
    top_k: int = 3,
    fusion_method: str = "rrf",
    sanitize_pii: bool = True,
) -> dict[str, str]:
    """Generate integration code snippets across 4 developer ecosystems."""
    curl_snippet = f"""curl -X POST {base_url}/api/v1/compress \\
  -H "Content-Type: application/json" \\
  -d '{{
    "history": [{{"role": "user", "content": "Deploying Postgres with PgBouncer."}}],
    "current_message": "How do I configure transaction pooling?",
    "top_k": {top_k},
    "target_model": "{target_model}",
    "compression_mode": "{compression_mode}",
    "fusion_method": "{fusion_method}",
    "sanitize_pii": {str(sanitize_pii).lower()}
  }}'"""

    python_snippet = f"""import httpx

payload = {{
    "history": [{{"role": "user", "content": "Deploying Postgres with PgBouncer."}}],
    "current_message": "How do I configure transaction pooling?",
    "top_k": {top_k},
    "target_model": "{target_model}",
    "compression_mode": "{compression_mode}",
    "fusion_method": "{fusion_method}",
    "sanitize_pii": {sanitize_pii},
}}

resp = httpx.post("{base_url}/api/v1/compress", json=payload, timeout=15.0)
data = resp.json()
print(f"Saved {{data['tokens_saved']}} tokens ({{data['compression_ratio']}}%)")"""

    ts_snippet = f"""const response = await fetch("{base_url}/api/v1/compress", {{
  method: "POST",
  headers: {{ "Content-Type": "application/json" }},
  body: JSON.stringify({{
    history: [{{ role: "user", content: "Deploying Postgres with PgBouncer." }}],
    current_message: "How do I configure transaction pooling?",
    top_k: {top_k},
    target_model: "{target_model}",
    compression_mode: "{compression_mode}",
    fusion_method: "{fusion_method}",
    sanitize_pii: {str(sanitize_pii).lower()}
  }})
}});
const optimized = await response.json();"""

    openai_proxy = f"""import httpx

# Drop-in OpenAI messages array compression
messages = [
    {{"role": "system", "content": "You are a senior SRE."}},
    {{"role": "user", "content": "Our EKS cluster uses Karpenter."}},
    {{"role": "assistant", "content": "Ensure IRSA permissions are attached."}},
    {{"role": "user", "content": "How do I debug pending pods?"}},
]

res = httpx.post("{base_url}/api/v1/chat/compress", json={{
    "messages": messages,
    "top_k": {top_k},
    "target_model": "{target_model}",
    "sanitize_pii": {sanitize_pii},
}}).json()

# Forward res["messages"] straight to OpenAI / Anthropic / Gemini!"""

    return {
        "curl": curl_snippet,
        "python": python_snippet,
        "typescript": ts_snippet,
        "openai_adapter": openai_proxy,
    }
