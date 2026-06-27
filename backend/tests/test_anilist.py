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

@patch('services.anilist.httpx.AsyncClient.post', new_callable=AsyncMock)
def test_get_anilist(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"Media": {"id": 1, "title": {"english": "Test"}}}
    }
    mock_post.return_value = mock_response
    
    response = client.get("/api/anilist/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@patch('services.anilist.httpx.AsyncClient.post', new_callable=AsyncMock)
def test_get_anilist_mal(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"Media": {"id": 1, "idMal": 123, "title": {"english": "Test MAL"}}}
    }
    mock_post.return_value = mock_response
    
    response = client.get("/api/anilist/123?id_type=mal")
    assert response.status_code == 200
    assert response.json()["id_mal"] == 123
    
    # Check if variables use 'id'
    called_json = mock_post.call_args[1]["json"]
    assert called_json["variables"]["id"] == 123

@patch('services.anilist.httpx.AsyncClient.post', new_callable=AsyncMock)
def test_get_anilist_missing_fields(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate API returning nulls for objects
    mock_response.json.return_value = {
        "data": {"Media": {"id": 2, "coverImage": None, "studios": None}}
    }
    mock_post.return_value = mock_response
    
    response = client.get("/api/anilist/2")
    assert response.status_code == 200
    data = response.json()
    assert data["cover_image"] is None
    assert data["studio"] is None

@patch('services.anilist.httpx.AsyncClient.post', new_callable=AsyncMock)
def test_get_anilist_404(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_post.return_value = mock_response
    
    response = client.get("/api/anilist/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "AniList media not found"
