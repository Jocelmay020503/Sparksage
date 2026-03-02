from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
import config
import db

router = APIRouter()


class ChannelProviderCreate(BaseModel):
    channel_id: str
    guild_id: str
    provider: str


@router.get("")
async def list_channel_providers(
    guild_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    items = await db.get_all_channel_providers(guild_id=guild_id)
    return {"channel_providers": items}


@router.get("/{channel_id}")
async def get_channel_provider(
    channel_id: str,
    user: dict = Depends(get_current_user),
):
    provider = await db.get_channel_provider(channel_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Channel provider override not found")
    return {"channel_id": channel_id, "provider": provider}


@router.post("")
async def create_channel_provider(
    body: ChannelProviderCreate,
    user: dict = Depends(get_current_user),
):
    if body.provider not in config.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {body.provider}")

    await db.set_channel_provider(body.channel_id, body.guild_id, body.provider)
    return {"status": "ok", "channel_id": body.channel_id, "provider": body.provider}


@router.delete("/{channel_id}")
async def delete_channel_provider(
    channel_id: str,
    user: dict = Depends(get_current_user),
):
    existing = await db.get_channel_provider(channel_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Channel provider override not found")

    await db.remove_channel_provider(channel_id)
    return {"status": "ok", "channel_id": channel_id}
