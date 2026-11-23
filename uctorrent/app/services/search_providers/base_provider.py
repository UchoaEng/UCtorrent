from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass
class SearchResult:
    name: str
    source: str
    magnet_uri: str | None = None
    torrent_url: str | None = None
    size: int | None = None
    seeders: int | None = None
    leechers: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class SearchProvider(Protocol):
    name: str
    enabled: bool

    def search(self, query: str, filters: dict | None = None) -> list[SearchResult]:
        ...
