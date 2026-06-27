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
