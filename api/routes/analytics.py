from fastapi import APIRouter, Depends
from api.deps import get_current_user
import db

router = APIRouter()


@router.get("/summary")
async def get_summary(days: int = 7, current_user: str = Depends(get_current_user)):
    """Get analytics summary for the specified number of days."""
    summary = await db.get_analytics_summary(days)
    return summary


@router.get("/history")
async def get_history(days: int = 7, event_type: str = None, current_user: str = Depends(get_current_user)):
    """Get analytics history with optional event type filter."""
    history = await db.get_analytics_history(days, event_type)
    return history


@router.get("/top-channels")
async def get_top_channels(limit: int = 10, current_user: str = Depends(get_current_user)):
    """Get top channels by usage."""
    channels = await db.get_top_channels(limit)
    return channels


@router.get("/top-users")
async def get_top_users(limit: int = 10, current_user: str = Depends(get_current_user)):
    """Get top users by usage."""
    users = await db.get_top_users(limit)
    return users
