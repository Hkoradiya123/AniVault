# backend/services/cache.py
from cachetools import TTLCache
import os

_caches = {}

def get_cache(name: str, default_ttl: int = 1800) -> TTLCache:
    if name not in _caches:
        ttl = int(os.getenv(f"CACHE_TTL_{name.upper()}", default_ttl))
        _caches[name] = TTLCache(maxsize=1000, ttl=ttl)
    return _caches[name]
