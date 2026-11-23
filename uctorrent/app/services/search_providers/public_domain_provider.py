from __future__ import annotations

from uctorrent.app.services.search_providers.base_provider import SearchResult


class PublicDomainProvider:
    name = "public-domain-examples"
    enabled = True

    def __init__(self):
        self._items = [
            SearchResult(
                name="Ubuntu ISO releases",
                source=self.name,
                torrent_url="https://ubuntu.com/download/alternative-downloads",
            ),
            SearchResult(
                name="Debian CD/DVD torrents",
                source=self.name,
                torrent_url="https://www.debian.org/CD/torrent-cd/",
            ),
            SearchResult(
                name="Public Domain Torrents catalog",
                source=self.name,
                torrent_url="https://publicdomaintorrents.info/",
            ),
        ]

    def search(self, query: str, filters: dict | None = None) -> list[SearchResult]:
        text = query.lower().strip()
        if not text:
            return []
        return [item for item in self._items if text in item.name.lower() or text in item.torrent_url.lower()]
