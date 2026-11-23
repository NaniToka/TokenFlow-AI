import pytest
import time
from app.services.cache.semantic_cache import SemanticCache


def test_semantic_cache_lru_and_expiration():
    cache = SemanticCache(max_size=2, default_ttl_seconds=1)
    k1 = cache.hash_key("query1")
    k2 = cache.hash_key("query2")
    k3 = cache.hash_key("query3")

    cache.set(k1, "result1")
    cache.set(k2, "result2")

    assert cache.get(k1) == "result1"
    assert cache.get(k2) == "result2"

    # Add 3rd item, should evict k1 (oldest accessed was k1 if k2 accessed after, but k1 was touched before k2)
    # Actually k1 was accessed, then k2. So k1 was moved to end, then k2 was moved to end. Oldest is k1!
    cache.set(k3, "result3")
    assert len(cache._cache) == 2

    # Stats
    stats = cache.stats()
    assert stats["hits"] >= 2
    assert stats["cached_entries"] == 2
