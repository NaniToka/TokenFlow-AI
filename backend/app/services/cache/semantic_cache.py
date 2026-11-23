"""
Semantic & In-Memory Embedding Cache with LRU Eviction.

Caches query embeddings and compression outputs by prompt hash or similarity
to bypass redundant LLM API calls and achieve sub-millisecond cache hits.
"""

import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0


class SemanticCache:
    """
    LRU Memory Cache for embedding vectors and compressed summaries.
    Enforces TTL expiration and capacity bounds.
    """

    def __init__(self, max_size: int = 2000, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    @staticmethod
    def hash_key(content: str) -> str:
        """Computes a SHA256 hex digest for cache key normalization."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieves value if present and not expired."""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]
        now = time.time()

        if now > entry.expires_at:
            del self._cache[key]
            self._misses += 1
            return None

        entry.hit_count += 1
        self._cache.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stores value with optional custom TTL, evicting oldest item if full."""
        now = time.time()
        ttl_seconds = ttl if ttl is not None else self.default_ttl

        if key in self._cache:
            self._cache.move_to_end(key)

        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + ttl_seconds,
            hit_count=0,
        )

        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry."""
        total = self._hits + self._misses
        hit_ratio = round((self._hits / total) * 100.0, 2) if total > 0 else 0.0
        return {
            "cached_entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio_pct": hit_ratio,
        }

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# Global cache singletons
embedding_cache = SemanticCache(max_size=5000, default_ttl_seconds=7200)
summary_cache = SemanticCache(max_size=1000, default_ttl_seconds=3600)
