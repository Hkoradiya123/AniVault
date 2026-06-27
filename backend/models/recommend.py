from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Any
from typing_extensions import Annotated

SafeStr = Annotated[str, StringConstraints(max_length=500)]

class UserProfile(BaseModel):
    watched: List[SafeStr] = []
    in_progress: List[SafeStr] = []
    liked_genres: Dict[SafeStr, int] = {}
    avg_completion_rate: Optional[float] = None
    ratings: Dict[SafeStr, int] = {}

class RecommendRequest(BaseModel):
    user_profile: UserProfile
    candidate_pool: List[Dict[str, Any]] = Field(..., max_length=60)
    exclude_ids: List[SafeStr] = []
    count: int = 6
    mood: Optional[str] = Field(default=None, max_length=500)

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    candidate_pool: List[Dict[str, Any]] = Field(..., max_length=60)

class SummaryRequest(BaseModel):
    anime_title: str = Field(..., max_length=200)
    episode_number: int
