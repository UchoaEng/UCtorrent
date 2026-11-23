from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.api.schemas import TagIn
from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import TagRepository


router = APIRouter(prefix="/api/tags", tags=["tags"], dependencies=[Depends(require_auth)])


@router.get("")
def list_tags():
    session = get_session()
    try:
        return [{"id": tag.id, "name": tag.name} for tag in TagRepository(session).list()]
    finally:
        session.close()


@router.post("")
def create_tag(payload: TagIn):
    session = get_session()
    try:
        tag = TagRepository(session).create(payload.name)
        session.commit()
        return {"id": tag.id, "name": tag.name}
    finally:
        session.close()


@router.delete("/{name}")
def delete_tag(name: str):
    session = get_session()
    try:
        TagRepository(session).delete(name)
        session.commit()
        return {"ok": True}
    finally:
        session.close()

