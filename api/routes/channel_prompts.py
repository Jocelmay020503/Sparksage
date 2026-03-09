from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
import db

router = APIRouter()


class ChannelPromptCreate(BaseModel):
    channel_id: str
    guild_id: str
    system_prompt: str


class ChannelPromptUpdate(BaseModel):
    system_prompt: str


@router.get("")
async def list_channel_prompts(
    guild_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """Get all channel prompts, optionally filtered by guild."""
    prompts = await db.get_all_channel_prompts(guild_id=guild_id)
    return {"channel_prompts": prompts}


@router.get("/{channel_id}")
async def get_channel_prompt(
    channel_id: str,
    user: dict = Depends(get_current_user),
):
    """Get the system prompt for a specific channel."""
    prompt_record = await db.get_channel_prompt_record(channel_id)
    if not prompt_record:
        raise HTTPException(status_code=404, detail="Channel prompt not found")
    return prompt_record


@router.post("")
async def create_channel_prompt(
    body: ChannelPromptCreate,
    user: dict = Depends(get_current_user),
):
    """Set or update a custom system prompt for a channel."""
    print(f"Creating channel prompt: channel_id={body.channel_id}, guild_id={body.guild_id}")
    await db.set_channel_prompt(
        body.channel_id,
        body.guild_id,
        body.system_prompt,
    )
    # Return the full record so dashboard can display it immediately
    prompt_record = await db.get_channel_prompt_record(body.channel_id)
    print(f"Saved successfully: {prompt_record}")
    return {"status": "ok", **prompt_record}


@router.put("/{channel_id}")
async def update_channel_prompt(
    channel_id: str,
    body: ChannelPromptUpdate,
    guild_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    """Update an existing channel prompt."""
    # Check if prompt exists
    existing = await db.get_channel_prompt(channel_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Channel prompt not found")
    
    await db.set_channel_prompt(channel_id, guild_id, body.system_prompt)
    return {"status": "ok", "channel_id": channel_id}


@router.delete("/{channel_id}")
async def delete_channel_prompt(
    channel_id: str,
    user: dict = Depends(get_current_user),
):
    """Remove a custom system prompt for a channel (revert to global)."""
    # Check if prompt exists
    existing = await db.get_channel_prompt(channel_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Channel prompt not found")
    
    await db.remove_channel_prompt(channel_id)
    return {"status": "ok", "channel_id": channel_id}
