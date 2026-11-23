from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import LogRepository


router = APIRouter(prefix="/api/logs", tags=["logs"], dependencies=[Depends(require_auth)])


@router.get("")
def logs(limit: int = 200):
    session = get_session()
    try:
        return [
            {
                "id": item.id,
                "level": item.level,
                "scope": item.scope,
                "message": item.message,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in LogRepository(session).list(limit)
        ]
    finally:
        session.close()

