"""Quota and rate limiting API endpoints."""

from fastapi import APIRouter, Depends, Query
import db

from api.auth import verify_token

router = APIRouter(tags=["quota"])


@router.get("/status")
async def get_quota_status(
    hours: int = Query(24, ge=1, le=720),
    _: dict = Depends(verify_token),
):
    """Get overall quota statistics for the past N hours."""
    stats = await db.get_quota_stats(hours=hours)
    return stats


@router.get("/violations")
async def get_quota_violations(
    hours: int = Query(24, ge=1, le=720),
    user_id: str | None = Query(None),
    guild_id: str | None = Query(None),
    _: dict = Depends(verify_token),
):
    """Get quota violations for the past N hours."""
    violations = await db.get_quota_violations(
        hours=hours,
        user_id=user_id,
        guild_id=guild_id,
    )
    return violations
