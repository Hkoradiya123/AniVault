from services.claude import get_recommendations, search_anime, summarize_episode
from models.recommend import UserProfile
from unittest.mock import patch, MagicMock

@patch("services.claude.client.messages.create")
def test_claude_recommend(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"1","title":"T","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = get_recommendations(UserProfile(), [], [], 1)
    assert res[0]["id"] == "1"

@patch("services.claude.client.messages.create")
def test_claude_recommend_mood(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"2","title":"T","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = get_recommendations(UserProfile(), [], [], 1, mood="action")
    assert res[0]["id"] == "2"

@patch("services.claude.client.messages.create")
def test_claude_recommend_exception(mock_create):
    mock_create.side_effect = Exception("API Error")
    
    res = get_recommendations(UserProfile(), [], [], 1)
    assert res == []

@patch("services.claude.client.messages.create")
def test_claude_search(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"3","title":"Search Match","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = search_anime("some query", [])
    assert res[0]["id"] == "3"

@patch("services.claude.client.messages.create")
def test_claude_search_exception(mock_create):
    mock_create.side_effect = Exception("API Error")
    
    res = search_anime("some query", [])
    assert res == []

@patch("services.claude.client.messages.create")
def test_claude_summarize(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='Summary text here.')]
    mock_create.return_value = mock_msg
    
    res = summarize_episode("Test Anime", 1)
    assert res == "Summary text here."

@patch("services.claude.client.messages.create")
def test_claude_summarize_exception(mock_create):
    mock_create.side_effect = Exception("API Error")
    
    res = summarize_episode("Test Anime", 1)
    assert res == "Summary unavailable for Test Anime episode 1."
