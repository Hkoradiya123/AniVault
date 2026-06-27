from fastapi import APIRouter, Request
from services.anilist import fetch_anilist_data
from core import limiter

router = APIRouter(prefix="/api/anilist")

@router.get("/{media_id}")
@limiter.limit("20/minute")
async def get_anilist(request: Request, media_id: int, id_type: str = "anilist"):
    return await fetch_anilist_data(media_id, id_type)
