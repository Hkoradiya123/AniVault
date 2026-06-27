from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

@patch('services.anikoto.httpx.AsyncClient.get', new_callable=AsyncMock)
def test_get_recent_anime(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ok": True,
        "pagination": {"page": 1, "per_page": 20, "total": 100},
        "data": []
    }
    mock_get.return_value = mock_response
    
    response = client.get("/api/recent?page=1")
    assert response.status_code == 200
    assert response.json()["ok"] is True
