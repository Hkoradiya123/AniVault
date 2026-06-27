import httpx
from services.cache import get_cache

BASE_URL = "https://anikotoapi.site"

async def fetch_recent(page: int, per_page: int) -> dict:
    cache = get_cache("recent")
    cache_key = f"{page}-{per_page}"
    
    if cache_key in cache:
        return cache[cache_key]
        
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/recent-anime?page={page}&per_page={per_page}")
        res.raise_for_status()
        data = res.json()
        cache[cache_key] = data
        return data

async def fetch_series(series_id: str) -> dict:
    cache = get_cache("series", default_ttl=7200)
    
    if series_id in cache:
        return cache[series_id]
        
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/series/{series_id}")
        res.raise_for_status()
        data = res.json()
        
        # Enrich with our structured MegaPlay URLs
        if "episodes" in data:
            for ep in data["episodes"]:
                embed_id = ep.get("episode_embed_id")
                ep["embed_url"] = {
                    "sub": f"https://megaplay.buzz/stream/s-2/{embed_id}/sub",
                    "dub": f"https://megaplay.buzz/stream/s-2/{embed_id}/dub" if data.get("anime", {}).get("has_dub") else None
                }
                
        cache[series_id] = data
        return data
