"""
HyDE (Hypothetical Document Embeddings) & Technical Query Expander.

Expands terse user queries with hypothetical answer terminology or curated
domain synonyms (Kubernetes, Postgres, Redis, Auth, ML, API) to improve recall.
Uses LLM generation when available and falls back to deterministic technical expansion.
"""

from __future__ import annotations

import re
from typing import Any

DOMAIN_EXPANSIONS: dict[str, list[str]] = {
    "k8s": ["kubernetes", "pod", "ingress", "kubectl", "eks", "deployment"],
    "kubernetes": ["k8s", "pod", "helm", "nodepool", "karpenter", "autoscaler"],
    "postgres": ["postgresql", "pgbouncer", "sql", "index", "vacuum", "pool"],
    "postgresql": ["postgres", "pgbouncer", "btree", "transaction", "isolation"],
    "db": ["database", "postgresql", "sql", "connection", "pool", "latency"],
    "auth": ["oauth2", "jwt", "token", "mtls", "oidc", "authentication"],
    "cache": ["redis", "lru", "ttl", "eviction", "memcache", "hit"],
    "redis": ["cache", "lru", "ttl", "pubsub", "eviction", "memory"],
    "rag": ["chunk", "embedding", "bm25", "vector", "retrieval", "semantic"],
    "llm": ["token", "prompt", "context", "summarization", "gemini", "model"],
    "timeout": ["latency", "retry", "backoff", "circuit", "breaker", "504"],
    "error": ["exception", "traceback", "500", "502", "failure", "debug"],
    "docker": ["container", "dockerfile", "image", "build", "alpine", "port"],
    "terraform": ["state", "lock", "dynamodb", "s3", "apply", "iac"],
}


class HyDEQueryExpander:
    """Generates expanded query representations for higher RAG & turn recall."""

    def __init__(self, llm_client: Any = None):
        self._llm = llm_client

    def expand(self, query: str, use_llm: bool = False) -> dict[str, Any]:
        """
        Expand query with domain terms and optional hypothetical passage.

        Returns:
            Dict containing original_query, expanded_query, added_terms, method.
        """
        clean_q = (query or "").strip()
        if not clean_q:
            return {
                "original_query": "",
                "expanded_query": "",
                "added_terms": [],
                "method": "none",
            }

        # Optional LLM HyDE passage generation
        if use_llm and self._llm and self._llm.is_available:
            prompt = (
                "Write a concise 2-sentence technical answer excerpt containing key terminology "
                f"for this engineering query:\n{clean_q}"
            )
            hypothetical = self._llm.summarize(prompt)
            if hypothetical:
                return {
                    "original_query": clean_q,
                    "expanded_query": f"{clean_q}\n{hypothetical}",
                    "added_terms": hypothetical.split()[:12],
                    "method": "llm_hyde",
                }

        # Deterministic domain synonym expansion
        tokens = re.findall(r"[a-z0-9_]+", clean_q.lower())
        existing = set(tokens)
        added: list[str] = []
        for tok in tokens:
            for syn in DOMAIN_EXPANSIONS.get(tok, []):
                if syn not in existing and syn not in added:
                    added.append(syn)
                if len(added) >= 8:
                    break
            if len(added) >= 8:
                break

        expanded = f"{clean_q} ({' '.join(added)})" if added else clean_q
        return {
            "original_query": clean_q,
            "expanded_query": expanded,
            "added_terms": added,
            "method": "domain_hyde_offline" if added else "identity",
        }
