from fastapi import APIRouter, Depends
from api.deps import get_current_user
import db

router = APIRouter()


@router.get("/summary")
async def get_cost_summary(days: int = 30, current_user: str = Depends(get_current_user)):
    """Get cost summary for the past N days."""
    summary = await db.get_cost_summary(days)
    return summary


@router.get("/by-provider")
async def get_cost_by_provider(days: int = 30, current_user: str = Depends(get_current_user)):
    """Get cost breakdown by provider."""
    costs = await db.get_cost_by_provider(days)
    return {"costs_by_provider": costs}


@router.get("/top-users")
async def get_top_users(days: int = 30, limit: int = 10, current_user: str = Depends(get_current_user)):
    """Get top expensive users."""
    users = await db.get_top_expensive_users(days, limit)
    return {"top_users": users}


@router.get("/top-guilds")
async def get_top_guilds(days: int = 30, limit: int = 10, current_user: str = Depends(get_current_user)):
    """Get top expensive guilds/servers."""
    guilds = await db.get_top_expensive_guilds(days, limit)
    return {"top_guilds": guilds}


@router.get("/history")
async def get_cost_history(days: int = 30, current_user: str = Depends(get_current_user)):
    """Get daily cost history."""
    history = await db.get_cost_history(days)
    return {"history": history}
