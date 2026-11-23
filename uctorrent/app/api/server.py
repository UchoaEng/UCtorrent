from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict, deque
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from uctorrent.app.api.auth import auth_service, require_auth
from uctorrent.app.api.routes_categories import router as categories_router
from uctorrent.app.api.routes_logs import router as logs_router
from uctorrent.app.api.routes_rss import router as rss_router
from uctorrent.app.api.routes_search import router as search_router
from uctorrent.app.api.routes_settings import router as settings_router
from uctorrent.app.api.routes_system import router as system_router
from uctorrent.app.api.routes_tags import router as tags_router
from uctorrent.app.api.routes_torrents import create_router as create_torrent_router
from uctorrent.app.api.schemas import LoginRequest
from uctorrent.app.core.torrent_manager import TorrentManager
from uctorrent.app.services.config_service import ConfigService
from uctorrent.app.utils.constants import APP_NAME, WEB_DIR


def create_app(manager: TorrentManager | None = None, config_service: ConfigService | None = None) -> FastAPI:
    config_service = config_service or ConfigService()
    manager = manager or TorrentManager(config_service.data)
    api_cfg = config_service.data.get("api", {})
    auth_service.username = api_cfg.get("username", "admin")
    auth_service.password = api_cfg.get("password", "admin")

    app = FastAPI(title=f"{APP_NAME} API")
    app.state.manager = manager
    app.state.config = config_service
    rate_limit = int(config_service.get("security.rate_limit_per_minute", 120))
    buckets: dict[str, deque[float]] = defaultdict(deque)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_cfg.get("cors_origins") or ["http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        if rate_limit > 0:
            client = request.client.host if request.client else "local"
            now = time.time()
            bucket = buckets[client]
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= rate_limit:
                from fastapi.responses import JSONResponse

                return JSONResponse({"detail": "Rate limit excedido."}, status_code=429)
            bucket.append(now)
        return await call_next(request)

    @app.post("/api/auth/login")
    def login(payload: LoginRequest):
        token = auth_service.login(payload.username, payload.password)
        return {"token": token, "username": payload.username}

    @app.post("/api/auth/logout")
    def logout(token: str = Depends(require_auth)):
        auth_service.logout(token)
        return {"ok": True}

    @app.get("/api/auth/me")
    def me(token: str = Depends(require_auth)):
        return {"username": auth_service.username}

    app.include_router(create_torrent_router(manager))
    app.include_router(categories_router)
    app.include_router(tags_router)
    app.include_router(rss_router)
    app.include_router(settings_router)
    app.include_router(system_router)
    app.include_router(search_router)
    app.include_router(logs_router)

    @app.websocket("/api/events")
    async def events(ws: WebSocket):
        await ws.accept()
        last_id = 0
        try:
            while True:
                events = manager.events.since(last_id)
                if events:
                    for item in events:
                        last_id = max(last_id, int(item["id"]))
                        await ws.send_json(item)
                else:
                    await asyncio.sleep(0.5)
        except Exception:
            return

    if WEB_DIR.exists():
        app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def webui():
        index = WEB_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return HTMLResponse(f"<h1>{APP_NAME}</h1>")

    return app


class ApiServerThread:
    def __init__(self, app: FastAPI, host: str, port: int):
        self.app = app
        self.host = host
        self.port = port
        self.thread: threading.Thread | None = None
        self.server: uvicorn.Server | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        config = self._create_config()
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True, name="UCtorrentAPI")
        self.thread.start()

    def _create_config(self) -> uvicorn.Config:
        return uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_config=None,
            log_level="warning",
            access_log=False,
        )

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
