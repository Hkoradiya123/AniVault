from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

@patch("routes.recommend.get_recommendations")
def test_recommend_route(mock_rec, client):
    mock_rec.return_value = [{"id": "1", "title": "Test", "reason": "Good"}]
    res = client.post("/api/recommend", json={
        "user_profile": {
            "watched": [],
            "in_progress": [],
            "liked_genres": {},
            "ratings": {}
        },
        "candidate_pool": [{"id": "1", "title": "Test"}],
        "count": 6
    })
    assert res.status_code == 200
    assert res.json()["recommendations"][0]["id"] == "1"

@patch("routes.recommend.search_anime")
def test_search_route(mock_search, client):
    mock_search.return_value = [{"id": "2", "title": "Search", "reason": "Match"}]
    res = client.post("/api/search", json={
        "query": "some query",
        "candidate_pool": [{"id": "2", "title": "Search"}]
    })
    assert res.status_code == 200
    assert res.json()["results"][0]["id"] == "2"

@patch("routes.recommend.summarize_episode")
def test_summary_route(mock_summary, client):
    mock_summary.return_value = "This is a recap."
    res = client.post("/api/summary", json={
        "anime_title": "Test Anime",
        "episode_number": 1
    })
    assert res.status_code == 200
    assert res.json()["summary"] == "This is a recap."
