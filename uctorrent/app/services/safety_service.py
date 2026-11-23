from __future__ import annotations

from pathlib import Path

from uctorrent.app.utils.constants import DANGEROUS_EXTENSIONS, LEGAL_NOTICE
from uctorrent.app.utils.file_utils import sanitize_filename
from uctorrent.app.utils.validators import (
    has_path_traversal,
    is_valid_http_url,
    is_valid_magnet,
    resolve_inside,
)


class SafetyService:
    legal_notice = LEGAL_NOTICE

    def validate_magnet(self, magnet_uri: str) -> None:
        if not is_valid_magnet(magnet_uri):
            raise ValueError("Magnet link invalido.")

    def validate_url(self, url: str) -> None:
        if not is_valid_http_url(url):
            raise ValueError("URL invalida. Use http ou https.")

    def validate_relative_path(self, path: str) -> None:
        if has_path_traversal(path):
            raise ValueError("Caminho com tentativa de path traversal.")

    def validate_save_path(self, base: Path, candidate: Path, require_confirmation: bool = False) -> Path:
        if require_confirmation:
            return candidate.resolve()
        return resolve_inside(base, candidate)

    def dangerous_files(self, paths: list[str | Path]) -> list[str]:
        found = []
        for path in paths:
            if Path(path).suffix.lower() in DANGEROUS_EXTENSIONS:
                found.append(str(path))
        return found

    def safe_filename(self, name: str) -> str:
        return sanitize_filename(name)

