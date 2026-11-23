from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MAGNET_RE = re.compile(r"^magnet:\?(.+)$", re.IGNORECASE)
INFO_HASH_RE = re.compile(r"^(?:urn:btih:)?([a-fA-F0-9]{40}|[A-Z2-7]{32})$")


def is_valid_magnet(uri: str) -> bool:
    if not uri or not MAGNET_RE.match(uri.strip()):
        return False
    query = urlparse(uri).query
    values = parse_qs(query).get("xt", [])
    return any(INFO_HASH_RE.match(value.replace("urn:btih:", "")) for value in values)


def is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def has_path_traversal(path: str | Path) -> bool:
    parts = Path(path).parts
    return any(part == ".." for part in parts)


def resolve_inside(base: Path, candidate: Path) -> Path:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if base_resolved == candidate_resolved:
        return candidate_resolved
    if base_resolved not in candidate_resolved.parents:
        raise ValueError(f"Caminho fora da pasta autorizada: {candidate}")
    return candidate_resolved

