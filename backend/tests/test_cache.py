# backend/tests/test_cache.py
from services.cache import get_cache

def test_cache_singleton():
    cache1 = get_cache("recent", default_ttl=60)
    cache2 = get_cache("recent", default_ttl=60)
    assert cache1 is cache2
    
    cache1["test"] = "data"
    assert cache2["test"] == "data"
