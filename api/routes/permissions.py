from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
import db

router = APIRouter()


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
    permissions = await db.list_permissions(guild_id=guild_id, command_name=command_name)
    return {"permissions": permissions}


@router.post("")
async def create_permission(body: PermissionCreate, user: dict = Depends(get_current_user)):
    """Add a role permission for a command."""
    await db.add_permission(
        command_name=body.command_name,
        guild_id=body.guild_id,
        role_id=body.role_id,
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
    deleted = await db.delete_permission(command_name, guild_id, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"status": "ok"}
