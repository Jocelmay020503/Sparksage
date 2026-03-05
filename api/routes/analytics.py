from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.deps import get_current_user
import db

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    guild_id: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    """Get summary analytics statistics."""
    summary = await db.get_analytics_summary(guild_id=guild_id, days=days)
    return summary


@router.get("/history")
async def get_analytics_history(
    guild_id: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    """Get daily analytics history for charts."""
    history = await db.get_analytics_history(guild_id=guild_id, days=days)
    return {"history": history}


@router.get("/top-channels")
async def get_top_channels(
    guild_id: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    """Get most active channels by event count."""
    channels = await db.get_top_channels_by_activity(guild_id=guild_id, days=days, limit=limit)
    return {"channels": channels}


@router.get("/providers")
async def get_provider_distribution(
    guild_id: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    """Get provider usage distribution."""
    providers = await db.get_provider_distribution(guild_id=guild_id, days=days)
    return {"providers": providers}
