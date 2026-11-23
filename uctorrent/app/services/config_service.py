from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from uctorrent.app.utils.constants import (
    APP_NAME,
    COMPLETED_DIR,
    CONFIG_PATH,
    INCOMPLETE_DIR,
    ensure_runtime_dirs,
)


DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "name": APP_NAME,
        "first_run_legal_notice_accepted": False,
        "theme": "system",
        "language": "pt-BR",
        "show_notifications": True,
    },
    "downloads": {
        "completed_path": str(COMPLETED_DIR),
        "incomplete_path": str(INCOMPLETE_DIR),
        "add_paused_by_default": False,
        "preallocate": False,
    },
    "bittorrent": {
        "listen_port": 6881,
        "random_port_on_start": False,
        "dht": True,
        "pex": True,
        "lsd": True,
        "utp": True,
        "encryption": "prefer",
        "source_recovery_trackers": [
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://open.stealth.si:80/announce",
            "udp://tracker.torrent.eu.org:451/announce",
            "udp://exodus.desync.com:6969/announce",
            "udp://open.demonii.com:1337/announce",
        ],
    },
    "queue": {
        "enabled": True,
        "max_active_downloads": 3,
        "max_active_uploads": 3,
        "max_active_torrents": 5,
    },
    "speed": {
        "download_limit": 0,
        "upload_limit": 0,
        "alternative_download_limit": 0,
        "alternative_upload_limit": 0,
        "alternative_enabled": False,
    },
    "api": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 8080,
        "username": "admin",
        "password": "admin",
        "cors_origins": ["http://127.0.0.1:8080"],
    },
    "rss": {
        "enabled": True,
        "auto_download": False,
        "check_interval": 300,
    },
    "security": {
        "allow_external_save_paths": False,
        "rate_limit_per_minute": 120,
    },
}


class ConfigService:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data = self.load()

    def load(self) -> dict[str, Any]:
        ensure_runtime_dirs()
        if not self.path.exists():
            self.save(DEFAULT_CONFIG)
            return deepcopy(DEFAULT_CONFIG)
        with self.path.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        merged = deepcopy(DEFAULT_CONFIG)
        self._deep_update(merged, loaded)
        return merged

    def save(self, data: dict[str, Any] | None = None) -> None:
        ensure_runtime_dirs()
        if data is not None:
            self.data = data
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, ensure_ascii=True)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        current: Any = self.data
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, dotted_key: str, value: Any) -> None:
        current = self.data
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
        self.save()

    @staticmethod
    def _deep_update(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                ConfigService._deep_update(target[key], value)
            else:
                target[key] = value
