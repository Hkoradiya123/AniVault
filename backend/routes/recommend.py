from fastapi import APIRouter, Request
from models.recommend import RecommendRequest, SearchRequest, SummaryRequest
from services.claude import get_recommendations, search_anime, summarize_episode

router = APIRouter(prefix="/api")

@router.post("/recommend")
async def recommend(request: Request, req: RecommendRequest):
    recs = get_recommendations(
        req.user_profile, 
        req.candidate_pool, 
        req.exclude_ids, 
        req.count, 
        req.mood
    )
    return {"ok": True, "recommendations": recs, "powered_by": "claude-sonnet-4-6"}

@router.post("/search")
async def search(request: Request, req: SearchRequest):
    results = search_anime(req.query, req.candidate_pool)
    return {"ok": True, "results": results}

@router.post("/summary")
async def summary(request: Request, req: SummaryRequest):
    text = summarize_episode(req.anime_title, req.episode_number)
    return {"ok": True, "summary": text}
