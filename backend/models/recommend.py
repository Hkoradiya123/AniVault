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
    mood: Optional[str] = Field(default=None, max_length=500)

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    candidate_pool: List[Dict[str, Any]] = Field(..., max_length=60)

class SummaryRequest(BaseModel):
    anime_title: str = Field(..., max_length=200)
    episode_number: int
