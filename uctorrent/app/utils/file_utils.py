from __future__ import annotations

import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name).strip()
    return cleaned or "arquivo"


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def free_space_bytes(path: Path) -> int:
    import shutil

    target = path if path.exists() else path.parent
    return shutil.disk_usage(target).free

