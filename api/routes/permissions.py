from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
import db

router = APIRouter()


def _normalize_command_name(command_name: str) -> str:
    normalized = " ".join((command_name or "").strip().split()).lower()
    while normalized.startswith("/"):
        normalized = normalized[1:].lstrip()
    return normalized


class PermissionCreate(BaseModel):
    command_name: str
    guild_id: str
    role_id: str


@router.get("")
async def list_permissions(
    guild_id: str | None = Query(default=None),
    command_name: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List all command permissions, optionally filtered by guild or command."""
    normalized_command = _normalize_command_name(command_name) if command_name is not None else None
    permissions = await db.list_permissions(guild_id=guild_id, command_name=normalized_command)
    return {"permissions": permissions}


@router.post("")
async def create_permission(body: PermissionCreate, user: dict = Depends(get_current_user)):
    """Add a role permission for a command."""
    command_name = _normalize_command_name(body.command_name)
    if not command_name:
        raise HTTPException(status_code=400, detail="command_name cannot be empty")

    await db.add_permission(
        command_name=command_name,
        guild_id=body.guild_id.strip(),
        role_id=body.role_id.strip(),
    )
    return {"status": "ok"}


@router.delete("")
async def delete_permission(
    command_name: str = Query(...),
    guild_id: str = Query(...),
    role_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    """Delete a role permission for a command."""
    normalized_command = _normalize_command_name(command_name)
    if not normalized_command:
        raise HTTPException(status_code=400, detail="command_name cannot be empty")

    deleted = await db.delete_permission(normalized_command, guild_id.strip(), role_id.strip())
    if not deleted:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"status": "ok"}
