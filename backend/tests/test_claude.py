from services.claude import get_recommendations, search_anime, summarize_episode
from models.recommend import UserProfile
from unittest.mock import patch, MagicMock
import pytest

@patch("services.claude._get_client")
def test_claude_recommend(mock_get_client):
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"1","title":"T","reason":"R"}]')]
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client
    
    profile = UserProfile(watched=["abc"])
    res = get_recommendations(profile, [{"id": "1"}], ["xyz"], 1)
    
    assert res[0]["id"] == "1"
    
    # Verify the prompt
    mock_client.messages.create.assert_called_once()
    args, kwargs = mock_client.messages.create.call_args
    assert "messages" in kwargs
    content = kwargs["messages"][0]["content"]
    assert "Based on this user profile" in content
    assert '{"watched":["abc"]' in content
    assert "xyz" in content

@patch("services.claude._get_client")
def test_claude_recommend_mood(mock_get_client):
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"2","title":"T","reason":"R"}]')]
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client
    
    res = get_recommendations(UserProfile(), [{"id": "2"}], [], 1, mood="action")
    
    assert res[0]["id"] == "2"
    
    # Verify the prompt
    mock_client.messages.create.assert_called_once()
    args, kwargs = mock_client.messages.create.call_args
    content = kwargs["messages"][0]["content"]
    assert "wants to watch something action" in content
    assert "Pick 1 anime" in content

@patch("services.claude._get_client")
def test_claude_search(mock_get_client):
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"id":"3","title":"Search Match","reason":"R"}]')]
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client
    
    res = search_anime("some query", [{"id": "3"}])
    
    assert res[0]["id"] == "3"
    
    # Verify the prompt
    mock_client.messages.create.assert_called_once()
    args, kwargs = mock_client.messages.create.call_args
    content = kwargs["messages"][0]["content"]
    assert "A user is searching for anime with this description: 'some query'" in content

@patch("services.claude._get_client")
def test_claude_summarize(mock_get_client):
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='Summary text here.')]
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client
    
    res = summarize_episode("Test Anime", 1)
    
    assert res == "Summary text here."
    
    # Verify the prompt
    mock_client.messages.create.assert_called_once()
    args, kwargs = mock_client.messages.create.call_args
    content = kwargs["messages"][0]["content"]
    assert "recap of episode 1 of the anime 'Test Anime'" in content

@patch("services.claude._get_client")
def test_claude_recommend_exception(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_get_client.return_value = mock_client
    
    with pytest.raises(Exception, match="API Error"):
        get_recommendations(UserProfile(), [{"id": "1"}], [], 1)

@patch("services.claude._get_client")
def test_claude_search_exception(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_get_client.return_value = mock_client
    
    with pytest.raises(Exception, match="API Error"):
        search_anime("some query", [{"id": "3"}])

@patch("services.claude._get_client")
def test_claude_summarize_exception(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_get_client.return_value = mock_client
    
    with pytest.raises(Exception, match="API Error"):
        summarize_episode("Test Anime", 1)
