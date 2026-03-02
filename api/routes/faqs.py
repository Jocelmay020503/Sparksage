from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_current_user
import db

router = APIRouter()


class FAQCreate(BaseModel):
    guild_id: str
    question: str
    answer: str
    match_keywords: str
    created_by: str | None = None


@router.get("")
async def list_faqs(
    guild_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    faqs = await db.list_faqs(guild_id=guild_id)
    return {"faqs": faqs}


@router.post("")
async def create_faq(body: FAQCreate, user: dict = Depends(get_current_user)):
    faq_id = await db.add_faq(
        guild_id=body.guild_id,
        question=body.question,
        answer=body.answer,
        match_keywords=body.match_keywords,
        created_by=body.created_by,
    )
    return {"id": faq_id, "status": "ok"}


@router.delete("/{faq_id}")
async def delete_faq(
    faq_id: int,
    guild_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    deleted = await db.delete_faq(faq_id, guild_id=guild_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"status": "ok"}
