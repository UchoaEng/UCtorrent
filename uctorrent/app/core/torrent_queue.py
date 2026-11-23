from __future__ import annotations


class TorrentQueue:
    def move_top(self, items: list[int], torrent_id: int) -> list[int]:
        return [torrent_id] + [item for item in items if item != torrent_id]

    def move_bottom(self, items: list[int], torrent_id: int) -> list[int]:
        return [item for item in items if item != torrent_id] + [torrent_id]

