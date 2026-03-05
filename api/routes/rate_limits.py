from __future__ import annotations

from fastapi import APIRouter, Depends

import config
from api.deps import get_current_user
from utils.rate_limiter import rate_limiter

router = APIRouter()


@router.get("/summary")
async def get_rate_limit_summary(user: dict = Depends(get_current_user)):
    """Get current quota usage snapshot for dashboard monitoring."""
    snapshot = await rate_limiter.get_quota_snapshot(top_n=10)
    return {
        "limits": {
            "user_requests_per_minute": config.RATE_LIMIT_USER,
            "guild_requests_per_minute": config.RATE_LIMIT_GUILD,
        },
        "usage": snapshot,
    }
