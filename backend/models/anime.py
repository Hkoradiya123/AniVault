# backend/models/anime.py
from pydantic import BaseModel
from typing import Any

class AnimeObject(BaseModel):
    id: str
    title: str
    cover_image: str
    genres: list[str]
    has_sub: bool
    has_dub: bool
    terms_by_type: dict[str, Any]

class EpisodeEmbed(BaseModel):
    sub: str
    dub: str | None = None

class Episode(BaseModel):
    index: int
    title: str
    episode_embed_id: str
    embed_url: EpisodeEmbed

class SeriesDetail(BaseModel):
    ok: bool
    anime: AnimeObject
    episodes: list[Episode]
