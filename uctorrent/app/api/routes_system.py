from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from uctorrent.app.api.auth import require_auth
from uctorrent.app.services.magnet_handler_service import magnet_handler_service


router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(require_auth)])


@router.post("/register-magnet-handler")
def register_magnet_handler(command: str | None = None):
    try:
        magnet_handler_service.register_windows(command or magnet_handler_service.default_command())
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/register-magnet-handler")
def unregister_magnet_handler():
    try:
        magnet_handler_service.unregister_windows()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
