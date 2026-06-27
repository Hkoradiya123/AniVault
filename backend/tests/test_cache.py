import pytest
from services.cache import get_cache, _caches
import os

@pytest.fixture(autouse=True)
def clean_cache():
    _caches.clear()
    yield
    _caches.clear()

def test_cache_singleton():
    cache1 = get_cache("recent", default_ttl=60)
    cache2 = get_cache("recent", default_ttl=60)
    assert cache1 is cache2
    
    cache1["test"] = "data"
    assert cache2["test"] == "data"

def test_cache_ttl_override(monkeypatch):
    monkeypatch.setenv("CACHE_TTL_RECENT", "120")
    cache = get_cache("recent", default_ttl=60)
    assert cache.ttl == 120
