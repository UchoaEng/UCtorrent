from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TorrentHandleWrapper:
    info_hash: str
    handle: Any

