from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.services.config_service import ConfigService


router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_auth)])
config_service = ConfigService()


@router.get("")
def get_settings():
    return config_service.data


@router.put("")
def put_settings(payload: dict):
    config_service.data = payload
    config_service.save()
    return config_service.data

