from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.api.schemas import CategoryIn
from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import CategoryRepository


router = APIRouter(prefix="/api/categories", tags=["categories"], dependencies=[Depends(require_auth)])


@router.get("")
def list_categories():
    session = get_session()
    try:
        return [{"id": item.id, "name": item.name, "save_path": item.save_path} for item in CategoryRepository(session).list()]
    finally:
        session.close()


@router.post("")
def create_category(payload: CategoryIn):
    session = get_session()
    try:
        item = CategoryRepository(session).upsert(payload.name, **payload.model_dump(exclude={"name"}))
        session.commit()
        return {"id": item.id, "name": item.name, "save_path": item.save_path}
    finally:
        session.close()


@router.put("/{name}")
def update_category(name: str, payload: CategoryIn):
    session = get_session()
    try:
        item = CategoryRepository(session).upsert(name, **payload.model_dump(exclude={"name"}))
        session.commit()
        return {"id": item.id, "name": item.name, "save_path": item.save_path}
    finally:
        session.close()


@router.delete("/{name}")
def delete_category(name: str):
    session = get_session()
    try:
        CategoryRepository(session).delete(name)
        session.commit()
        return {"ok": True}
    finally:
        session.close()

