from __future__ import annotations

import re
from pathlib import Path

from uctorrent.app.utils.validators import is_valid_magnet


MAGNET_IN_TEXT_RE = re.compile(r"magnet:\?[^\s\"'<>]+", re.IGNORECASE)
TEXT_MAGNET_EXTENSIONS = {".magnet", ".txt", ".url"}
MAX_MAGNET_TEXT_BYTES = 2 * 1024 * 1024


def extract_magnets(text: str) -> list[str]:
    magnets: list[str] = []
    seen = set()
    for match in MAGNET_IN_TEXT_RE.findall(text or ""):
        magnet = match.strip().rstrip(").,;]")
        if magnet not in seen and is_valid_magnet(magnet):
            magnets.append(magnet)
            seen.add(magnet)
    return magnets


def extract_magnets_from_file(path: str | Path) -> list[str]:
    file_path = Path(path)
    if file_path.suffix.lower() not in TEXT_MAGNET_EXTENSIONS:
        return []
    if not file_path.exists() or file_path.stat().st_size > MAX_MAGNET_TEXT_BYTES:
        return []
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return extract_magnets(text)
