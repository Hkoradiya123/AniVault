import httpx
from services.cache import get_cache
from fastapi import HTTPException
import re

URL = "https://graphql.anilist.co"
QUERY = """
query ($id: Int, $type: MediaType) {
  Media (id: $id, type: $type) {
    id
    idMal
    title { english romaji native }
    description(asHtml: false)
    coverImage { extraLarge }
    bannerImage
    averageScore
    episodes
    duration
    status
    season
    seasonYear
    genres
    studios(isMain: true) { nodes { name } }
    trailer { id site }
  }
}
"""

def strip_html(text: str) -> str:
    if not text: return ""
    return re.sub('<[^<]+>', '', text)

async def fetch_anilist_data(media_id: int, id_type: str = "anilist"):
    cache = get_cache("anilist", default_ttl=21600)
    cache_key = f"{id_type}-{media_id}"
    
    if cache_key in cache:
        return cache[cache_key]
        
    variables = {"id": media_id, "type": "ANIME"}
    if id_type == "mal":
        query_to_use = QUERY.replace("id: $id", "idMal: $id")
    else:
        query_to_use = QUERY

    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(URL, json={"query": query_to_use, "variables": variables})
        if res.status_code == 404:
            raise HTTPException(status_code=404, detail="AniList media not found")
        res.raise_for_status()
        
        data = (res.json().get("data") or {}).get("Media") or {}
        
        if not data:
            raise HTTPException(status_code=404, detail="AniList media not found")
            
        result = {
            "id": data.get("id"),
            "id_mal": data.get("idMal"),
            "title": data.get("title") or {},
            "description": strip_html(data.get("description", "")),
            "cover_image": (data.get("coverImage") or {}).get("extraLarge"),
            "banner_image": data.get("bannerImage"),
            "score": data.get("averageScore"),
            "episodes": data.get("episodes"),
            "duration": data.get("duration"),
            "status": data.get("status"),
            "season": data.get("season"),
            "season_year": data.get("seasonYear"),
            "genres": data.get("genres") or [],
            "studio": ((data.get("studios") or {}).get("nodes") or [{}])[0].get("name") if (data.get("studios") or {}).get("nodes") else None,
            "trailer": data.get("trailer")
        }
        
        cache[cache_key] = result
        return result
