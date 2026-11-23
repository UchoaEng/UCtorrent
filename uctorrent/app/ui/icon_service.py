from __future__ import annotations

from PySide6.QtGui import QIcon

from uctorrent.app.utils.constants import ICONS_DIR


ICON_NAMES = [
    "activity",
    "category",
    "download",
    "folder",
    "magnet",
    "pause",
    "play",
    "queue",
    "recover",
    "refresh",
    "remove",
    "rss",
    "search",
    "settings",
    "tag",
    "torrent",
    "tracker",
    "upload",
    "warning",
]


class IconService:
    _cache: dict[str, QIcon] = {}

    @classmethod
    def icon(cls, name: str) -> QIcon:
        if name not in cls._cache:
            cls._cache[name] = QIcon(str(ICONS_DIR / f"{name}.svg"))
        return cls._cache[name]
