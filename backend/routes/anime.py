from fastapi import APIRouter, Request
from services.anikoto import fetch_recent, fetch_series
from core import limiter

router = APIRouter(prefix="/api")

@router.get("/recent")
@limiter.limit("20/minute")
async def get_recent(request: Request, page: int = 1, per_page: int = 20) -> dict:
    return await fetch_recent(page, per_page)

@router.get("/series/{series_id}")
@limiter.limit("20/minute")
async def get_series(request: Request, series_id: str) -> dict:
    return await fetch_series(series_id)
