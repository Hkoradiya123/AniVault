from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
import pytest
from services.cache import _caches

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_cache():
    _caches.clear()
    yield
    _caches.clear()

@patch('services.anikoto.httpx.AsyncClient.get', new_callable=AsyncMock)
def test_get_recent_anime(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ok": True,
        "pagination": {"page": 1, "per_page": 20, "total": 100},
        "data": [{
            "id": "1",
            "title": "Test Anime",
            "cover_image": "img.jpg",
            "genres": ["Action"],
            "has_sub": True,
            "has_dub": False,
            "terms_by_type": {}
        }]
    }
    mock_get.return_value = mock_response
    
    response = client.get("/api/recent?page=1")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["data"][0]["title"] == "Test Anime"

@patch('services.anikoto.httpx.AsyncClient.get', new_callable=AsyncMock)
def test_get_series_anime(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ok": True,
        "anime": {
            "id": "1",
            "title": "Test Series",
            "cover_image": "img.jpg",
            "genres": ["Action"],
            "has_sub": True,
            "has_dub": True,
            "terms_by_type": {}
        },
        "episodes": [{
            "index": 1,
            "title": "Ep 1",
            "episode_embed_id": "12345",
        }]
    }
    mock_get.return_value = mock_response
    
    response = client.get("/api/series/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["episodes"][0]["embed_url"]["sub"] == "https://megaplay.buzz/stream/s-2/12345/sub"
    assert data["episodes"][0]["embed_url"]["dub"] == "https://megaplay.buzz/stream/s-2/12345/dub"

@patch('services.anikoto.httpx.AsyncClient.get', new_callable=AsyncMock)
def test_get_series_no_dub(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ok": True,
        "anime": {
            "id": "2",
            "title": "Test Series No Dub",
            "cover_image": "img.jpg",
            "genres": ["Action"],
            "has_sub": True,
            "has_dub": False,
            "terms_by_type": {}
        },
        "episodes": [{
            "index": 1,
            "title": "Ep 1",
            "episode_embed_id": "54321",
        }]
    }
    mock_get.return_value = mock_response
    
    response = client.get("/api/series/2")
    assert response.status_code == 200
    data = response.json()
    assert data["episodes"][0]["embed_url"]["sub"] == "https://megaplay.buzz/stream/s-2/54321/sub"
    assert data["episodes"][0]["embed_url"]["dub"] is None

@patch('services.anikoto.httpx.AsyncClient.get', new_callable=AsyncMock)
def test_get_series_not_found(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    response = client.get("/api/series/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Series not found"
