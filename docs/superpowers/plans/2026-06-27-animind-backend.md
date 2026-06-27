# AniMind Backend API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend proxy with caching, external API integrations (Anikoto, AniList), and Anthropic Claude AI features.

**Architecture:** A FastAPI application structured with modular routes, services for external API calls, and Pydantic models for validation. We use in-memory `cachetools` to aggressively cache Anikoto, AniList, and Anthropic responses to reduce latency and API limits. `slowapi` provides rate limiting per IP. 

**Tech Stack:** FastAPI, uvicorn, httpx, anthropic, cachetools, python-dotenv, pydantic, slowapi, pytest

## Global Constraints

- Python version: 3.11+
- CORS limited to `ALLOWED_ORIGINS` from env.
- API Keys stored in `.env` (never hardcoded or exposed).
- Rate limits applied per route using `slowapi`.
- All routes return generic 500 errors on unhandled exceptions (no internal details exposed).
- All AI inputs sanitized/capped at 500 chars.

---

### Task 1: Project Scaffolding and Health Route

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/tests/test_health.py`
- Create: `backend/main.py`
- Create: `backend/routes/health.py`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces: FastAPI `app` instance with CORS and rate limiter configured. `GET /health` endpoint.

- [ ] **Step 1: Write requirements and scaffolding setup**

```text
# backend/requirements.txt
fastapi
uvicorn
httpx
anthropic
cachetools
python-dotenv
pydantic
slowapi
pytest
pytest-asyncio
httpx[cli]
```

Run: `cd backend && pip install -r requirements.txt`

- [ ] **Step 2: Write the failing test for health check**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

# backend/tests/test_health.py
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL with ModuleNotFoundError for 'main'

- [ ] **Step 4: Write minimal implementation**

```python
# backend/routes/health.py
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
```

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from routes.health import router as health_router

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AniMind Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd backend
git add requirements.txt tests/ main.py routes/
git commit -m "chore: initial fastapi setup with health check"
```

---

### Task 2: Models and Cache Service

**Files:**
- Create: `backend/models/anime.py`
- Create: `backend/services/cache.py`
- Create: `backend/tests/test_cache.py`

**Interfaces:**
- Produces: `get_cache(name: str)` function, `AnimeObject` and `SeriesDetail` Pydantic models.

- [ ] **Step 1: Write the failing test for cache service**

```python
# backend/tests/test_cache.py
from services.cache import get_cache

def test_cache_singleton():
    cache1 = get_cache("recent", ttl=60)
    cache2 = get_cache("recent", ttl=60)
    assert cache1 is cache2
    
    cache1["test"] = "data"
    assert cache2["test"] == "data"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_cache.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/cache.py
from cachetools import TTLCache
import os

_caches = {}

def get_cache(name: str, default_ttl: int = 1800) -> TTLCache:
    if name not in _caches:
        ttl = int(os.getenv(f"CACHE_TTL_{name.upper()}", default_ttl))
        _caches[name] = TTLCache(maxsize=1000, ttl=ttl)
    return _caches[name]
```

```python
# backend/models/anime.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AnimeObject(BaseModel):
    id: str
    title: str
    cover_image: str
    genres: List[str]
    has_sub: bool
    has_dub: bool
    terms_by_type: Dict[str, Any]

class EpisodeEmbed(BaseModel):
    sub: str
    dub: Optional[str] = None

class Episode(BaseModel):
    index: int
    title: str
    episode_embed_id: str
    embed_url: EpisodeEmbed

class SeriesDetail(BaseModel):
    ok: bool
    anime: AnimeObject
    episodes: List[Episode]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_cache.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add models/ services/ tests/
git commit -m "feat: add pydantic models and cache service"
```

---

### Task 3: Anikoto Service and Anime Routes

**Files:**
- Create: `backend/services/anikoto.py`
- Create: `backend/routes/anime.py`
- Modify: `backend/main.py:30` (include router)
- Create: `backend/tests/test_anime.py`

**Interfaces:**
- Consumes: `get_cache` and `AnimeObject`, `SeriesDetail` models
- Produces: `GET /api/recent`, `GET /api/series/{id}`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_anime.py
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

@patch('services.anikoto.httpx.AsyncClient.get')
def test_get_recent_anime(mock_get, client):
    mock_get.return_value = AsyncMock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "ok": True,
        "pagination": {"page": 1, "per_page": 20, "total": 100},
        "data": []
    }
    
    response = client.get("/api/recent?page=1")
    assert response.status_code == 200
    assert response.json()["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_anime.py -v`
Expected: FAIL (route not found or module not found)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/anikoto.py
import httpx
from services.cache import get_cache

BASE_URL = "https://anikotoapi.site"

async def fetch_recent(page: int, per_page: int):
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

async def fetch_series(series_id: str):
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
```

```python
# backend/routes/anime.py
from fastapi import APIRouter, Request
from services.anikoto import fetch_recent, fetch_series

router = APIRouter(prefix="/api")

@router.get("/recent")
async def get_recent(request: Request, page: int = 1, per_page: int = 20):
    return await fetch_recent(page, per_page)

@router.get("/series/{series_id}")
async def get_series(request: Request, series_id: str):
    return await fetch_series(series_id)
```

Modify `backend/main.py`:
```python
# Add to imports
from routes.anime import router as anime_router

# Add before app.include_router(health_router)
app.include_router(anime_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_anime.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add services/anikoto.py routes/anime.py main.py tests/test_anime.py
git commit -m "feat: add anikoto service and anime routes"
```

---

### Task 4: AniList GraphQL Service and Route

**Files:**
- Create: `backend/services/anilist.py`
- Create: `backend/routes/anilist.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_anilist.py`

**Interfaces:**
- Produces: `GET /api/anilist/{id}`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_anilist.py
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

@patch('services.anilist.httpx.AsyncClient.post')
def test_get_anilist(mock_post, client):
    mock_post.return_value = AsyncMock()
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {"Media": {"id": 1, "title": {"english": "Test"}}}
    }
    
    response = client.get("/api/anilist/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_anilist.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/anilist.py
import httpx
from services.cache import get_cache
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
        variables = {"idMal": media_id, "type": "ANIME"}
        query_mal = QUERY.replace("id: $id", "idMal: $id")
    else:
        query_mal = QUERY

    async with httpx.AsyncClient() as client:
        res = await client.post(URL, json={"query": query_mal, "variables": variables})
        res.raise_for_status()
        data = res.json().get("data", {}).get("Media", {})
        
        if not data:
            return {}
            
        result = {
            "id": data.get("id"),
            "id_mal": data.get("idMal"),
            "title": data.get("title", {}),
            "description": strip_html(data.get("description", "")),
            "cover_image": data.get("coverImage", {}).get("extraLarge"),
            "banner_image": data.get("bannerImage"),
            "score": data.get("averageScore"),
            "episodes": data.get("episodes"),
            "duration": data.get("duration"),
            "status": data.get("status"),
            "season": data.get("season"),
            "season_year": data.get("seasonYear"),
            "genres": data.get("genres", []),
            "studio": data.get("studios", {}).get("nodes", [{}])[0].get("name") if data.get("studios", {}).get("nodes") else None,
            "trailer": data.get("trailer")
        }
        
        cache[cache_key] = result
        return result
```

```python
# backend/routes/anilist.py
from fastapi import APIRouter, Request
from services.anilist import fetch_anilist_data

router = APIRouter(prefix="/api/anilist")

@router.get("/{media_id}")
async def get_anilist(request: Request, media_id: int, id_type: str = "anilist"):
    return await fetch_anilist_data(media_id, id_type)
```

Modify `backend/main.py`:
```python
from routes.anilist import router as anilist_router
app.include_router(anilist_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_anilist.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add services/anilist.py routes/anilist.py main.py tests/test_anilist.py
git commit -m "feat: add anilist graphql integration"
```

---

### Task 5: Claude AI Service and Models

**Files:**
- Create: `backend/models/recommend.py`
- Create: `backend/services/claude.py`
- Create: `backend/tests/test_claude.py`

**Interfaces:**
- Produces: `UserProfile`, `RecommendRequest`, `SearchRequest`, `SummaryRequest` models, and Claude wrapper methods.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_claude.py
from services.claude import get_recommendations
from models.recommend import UserProfile
from unittest.mock import patch, MagicMock

@patch("services.claude.client.messages.create")
def test_claude_recommend(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"1","title":"T","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = get_recommendations(UserProfile(), [], [], 1)
    assert res[0]["id"] == "1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_claude.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/models/recommend.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class UserProfile(BaseModel):
    watched: List[str] = []
    in_progress: List[str] = []
    liked_genres: Dict[str, int] = {}
    avg_completion_rate: Optional[float] = None
    ratings: Dict[str, int] = {}

class RecommendRequest(BaseModel):
    user_profile: UserProfile
    candidate_pool: List[Dict[str, Any]] = Field(..., max_length=60)
    exclude_ids: List[str] = []
    count: int = 6
    mood: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    candidate_pool: List[Dict[str, Any]] = Field(..., max_length=60)

class SummaryRequest(BaseModel):
    anime_title: str = Field(..., max_length=200)
    episode_number: int
```

```python
# backend/services/claude.py
import anthropic
import os
import json
from models.recommend import UserProfile
from typing import List, Dict, Any

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "dummy"))

def get_recommendations(profile: UserProfile, pool: List[Dict[str, Any]], exclude: List[str], count: int, mood: str = None) -> List[Dict[str, Any]]:
    if mood:
        prompt = f"Pick {count} anime from this pool for a user who wants to watch something {mood}. Pool: {pool}. Exclude IDs: {exclude}. Return ONLY JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"...\"}}]. No other text."
    else:
        prompt = f"You are an anime recommendation engine. Based on this user profile: {profile.model_dump_json()}. From this pool of anime: {pool}. Pick exactly {count} anime the user would most enjoy. Exclude these IDs: {exclude}. Return ONLY a JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"one sentence why this fits the user\"}}]. No other text."
        
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        return json.loads(msg.content[0].text)
    except Exception:
        return []

def search_anime(query: str, pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prompt = f"A user is searching for anime with this description: '{query}'. From this pool: {pool}. Return the top 6 matches as ONLY a JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"why it matches the query\"}}]. No other text."
    
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        return json.loads(msg.content[0].text)
    except Exception:
        return []

def summarize_episode(title: str, ep_num: int) -> str:
    prompt = f"Give a 3-sentence spoiler-free recap of episode {ep_num} of the anime '{title}'. Focus on the main events without revealing major twists. Keep it under 80 words. Plain text only, no markdown."
    
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return msg.content[0].text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_claude.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add models/recommend.py services/claude.py tests/test_claude.py
git commit -m "feat: add anthropic claude models and wrapper methods"
```

---

### Task 6: AI Routes

**Files:**
- Create: `backend/routes/recommend.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_recommend.py`

**Interfaces:**
- Produces: `POST /api/recommend`, `POST /api/search`, `POST /api/summary`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_recommend.py
from fastapi.testclient import TestClient
from unittest.mock import patch

@patch("routes.recommend.get_recommendations")
def test_recommend_route(mock_rec, client):
    mock_rec.return_value = [{"id": "1", "title": "Test", "reason": "Good"}]
    res = client.post("/api/recommend", json={
        "user_profile": {},
        "candidate_pool": [],
        "count": 6
    })
    assert res.status_code == 200
    assert res.json()["recommendations"][0]["id"] == "1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_recommend.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/routes/recommend.py
from fastapi import APIRouter, Request
from models.recommend import RecommendRequest, SearchRequest, SummaryRequest
from services.claude import get_recommendations, search_anime, summarize_episode

router = APIRouter(prefix="/api")

@router.post("/recommend")
async def recommend(request: Request, req: RecommendRequest):
    recs = get_recommendations(
        req.user_profile, 
        req.candidate_pool, 
        req.exclude_ids, 
        req.count, 
        req.mood
    )
    return {"ok": True, "recommendations": recs, "powered_by": "claude-sonnet-4-6"}

@router.post("/search")
async def search(request: Request, req: SearchRequest):
    results = search_anime(req.query, req.candidate_pool)
    return {"ok": True, "results": results}

@router.post("/summary")
async def summary(request: Request, req: SummaryRequest):
    text = summarize_episode(req.anime_title, req.episode_number)
    return {"ok": True, "summary": text}
```

Modify `backend/main.py`:
```python
from routes.recommend import router as recommend_router
app.include_router(recommend_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_recommend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add routes/recommend.py main.py tests/test_recommend.py
git commit -m "feat: add AI endpoints for recommend, search, and summary"
```

---

End of backend implementation plan.
