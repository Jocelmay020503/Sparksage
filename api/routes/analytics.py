"""Analytics API endpoints for usage tracking and reporting."""

from fastapi import APIRouter, Depends, Query
import db

from api.auth import verify_token

router = APIRouter(tags=["analytics"])


@router.get("/summary")
async def get_summary(
    days: int = Query(7, ge=1, le=90),
    _: dict = Depends(verify_token),
):
    """Get analytics summary for the past N days."""
    summary = await db.get_analytics_summary(days=days)
    return summary


@router.get("/history")
async def get_history(
    days: int = Query(7, ge=1, le=90),
    event_type: str | None = Query(None),
    _: dict = Depends(verify_token),
):
    """Get analytics history with daily aggregation."""
    history = await db.get_analytics_history(days=days, event_type=event_type)
    return history


@router.get("/top-channels")
async def get_top_channels(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(verify_token),
):
    """Get most active channels by event count."""
    channels = await db.get_top_channels(limit=limit)
    return channels


@router.get("/top-users")
async def get_top_users(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(verify_token),
):
    """Get most active users by event count."""
    users = await db.get_top_users(limit=limit)
    return users
