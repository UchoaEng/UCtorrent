from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.services.search_service import SearchService


router = APIRouter(prefix="/api/search", tags=["search"], dependencies=[Depends(require_auth)])
search_service = SearchService()


@router.get("")
def search(q: str, provider: str | None = None):
    return {
        "legal_notice": "Use apenas fontes legais ou autorizadas.",
        "providers": search_service.list_providers(),
        "results": search_service.search(q, provider),
    }


@router.get("/providers")
def providers():
    return {"providers": search_service.list_providers()}
