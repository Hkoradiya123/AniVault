from fastapi import APIRouter, Request
from datetime import datetime, timezone
from core import limiter

router = APIRouter()

@router.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
