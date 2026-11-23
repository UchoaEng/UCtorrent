from __future__ import annotations


def aggregate_speeds(torrents: list[dict]) -> dict[str, int]:
    return {
        "download_rate": sum(int(item.get("download_rate") or 0) for item in torrents),
        "upload_rate": sum(int(item.get("upload_rate") or 0) for item in torrents),
        "active": sum(1 for item in torrents if item.get("status") in {"downloading", "seeding", "metadata"}),
    }

