from __future__ import annotations

from uctorrent.app.utils.formatters import display_text


def peer_to_dict(peer) -> dict:
    return {
        "ip": display_text(getattr(peer, "ip", "")),
        "port": getattr(peer, "port", 0),
        "client": display_text(getattr(peer, "client", "")),
        "progress": getattr(peer, "progress", 0.0),
    }
