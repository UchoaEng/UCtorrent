from __future__ import annotations

from uctorrent.app.utils.formatters import display_text


STATUS_FILTERS = {
    "Todos": None,
    "Baixando": {"downloading", "metadata", "checking", "queued"},
    "Semeando": {"seeding"},
    "Finalizados": {"finished", "seeding"},
    "Pausados": {"paused"},
    "Ativos": {"downloading", "metadata", "seeding", "checking"},
    "Inativos": {"paused", "finished", "offline"},
    "Com erro": {"error", "offline", "no_seeds"},
}


def filter_torrents(
    torrents: list[dict],
    text: str = "",
    status: str | set[str] | None = None,
    category: str | None = None,
    tag: str | None = None,
) -> list[dict]:
    text = text.lower().strip()
    result = []
    for torrent in torrents:
        searchable = " ".join(
            [
                display_text(torrent.get("name") or ""),
                display_text(torrent.get("info_hash") or ""),
                display_text(torrent.get("category") or ""),
                " ".join(display_text(tag) for tag in (torrent.get("tags") or [])),
                display_text(torrent.get("tracker") or ""),
            ]
        ).lower()
        if text and text not in searchable:
            continue
        if isinstance(status, set) and torrent.get("status") not in status:
            continue
        if isinstance(status, str) and torrent.get("status") != status:
            continue
        if category and torrent.get("category") != category:
            continue
        if tag and tag not in (torrent.get("tags") or []):
            continue
        result.append(torrent)
    return result
