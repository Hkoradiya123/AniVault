import anthropic
import json
import os
from models.recommend import UserProfile
from typing import List, Dict, Any

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "dummy"))

def _call_claude_json(prompt: str) -> List[Dict[str, Any]]:
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

def get_recommendations(profile: UserProfile, pool: List[Dict[str, Any]], exclude: List[str], count: int, mood: str = None) -> List[Dict[str, Any]]:
    if mood:
        prompt = f"Pick {count} anime from this pool for a user who wants to watch something {mood}. Pool: {pool}. Exclude IDs: {exclude}. Return ONLY JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"...\"}}]. No other text."
    else:
        prompt = f"You are an anime recommendation engine. Based on this user profile: {profile.model_dump_json()}. From this pool of anime: {pool}. Pick exactly {count} anime the user would most enjoy. Exclude these IDs: {exclude}. Return ONLY a JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"one sentence why this fits the user\"}}]. No other text."
        
    return _call_claude_json(prompt)

def search_anime(query: str, pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prompt = f"A user is searching for anime with this description: '{query}'. From this pool: {pool}. Return the top 6 matches as ONLY a JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"reason\": \"why it matches the query\"}}]. No other text."
    
    return _call_claude_json(prompt)

def summarize_episode(title: str, ep_num: int) -> str:
    prompt = f"Give a 3-sentence spoiler-free recap of episode {ep_num} of the anime '{title}'. Focus on the main events without revealing major twists. Keep it under 80 words. Plain text only, no markdown."
    
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text
