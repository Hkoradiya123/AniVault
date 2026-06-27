from services.claude import get_recommendations, search_anime, summarize_episode
from models.recommend import UserProfile
from unittest.mock import patch, MagicMock
import pytest

@patch("services.claude.client.messages.create")
def test_claude_recommend(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"1","title":"T","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    profile = UserProfile(watched=["abc"])
    res = get_recommendations(profile, [{"id": "1"}], ["xyz"], 1)
    
    assert res[0]["id"] == "1"
    
    # Verify the prompt
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert "messages" in kwargs
    content = kwargs["messages"][0]["content"]
    assert "Based on this user profile" in content
    assert '{"watched":["abc"]' in content
    assert "xyz" in content

@patch("services.claude.client.messages.create")
def test_claude_recommend_mood(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"2","title":"T","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = get_recommendations(UserProfile(), [{"id": "2"}], [], 1, mood="action")
    
    assert res[0]["id"] == "2"
    
    # Verify the prompt
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    content = kwargs["messages"][0]["content"]
    assert "wants to watch something action" in content
    assert "Pick 1 anime" in content

@patch("services.claude.client.messages.create")
def test_claude_search(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"3","title":"Search Match","reason":"R"}]')]
    mock_create.return_value = mock_msg
    
    res = search_anime("some query", [{"id": "3"}])
    
    assert res[0]["id"] == "3"
    
    # Verify the prompt
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    content = kwargs["messages"][0]["content"]
    assert "A user is searching for anime with this description: 'some query'" in content

@patch("services.claude.client.messages.create")
def test_claude_summarize(mock_create):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='Summary text here.')]
    mock_create.return_value = mock_msg
    
    res = summarize_episode("Test Anime", 1)
    
    assert res == "Summary text here."
    
    # Verify the prompt
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    content = kwargs["messages"][0]["content"]
    assert "recap of episode 1 of the anime 'Test Anime'" in content
