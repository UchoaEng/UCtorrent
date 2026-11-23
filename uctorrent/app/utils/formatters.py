from __future__ import annotations

import locale
from pathlib import Path
from typing import Any


def display_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _bytes_to_text(bytes(value), default)
    return str(value)


def _bytes_to_text(value: bytes, default: str) -> str:
    if not value:
        return default
    encodings = ["utf-8", locale.getpreferredencoding(False), "latin-1"]
    for encoding in dict.fromkeys(encodings):
        try:
            text = value.decode(encoding)
        except UnicodeDecodeError:
            continue
        if _looks_like_text(text):
            return text
    return value.hex()


def _looks_like_text(value: str) -> bool:
    if "\x00" in value:
        return False
    control_chars = sum(1 for char in value if ord(char) < 32 and char not in "\r\n\t")
    replacement_chars = value.count("\ufffd")
    return control_chars + replacement_chars <= max(1, len(value) // 10)


def format_bytes(value: int | float | None) -> str:
    if value is None:
        return "0 B"
    size = float(max(value, 0))
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def format_speed(value: int | float | None) -> str:
    return f"{format_bytes(value)}/s"


def format_ratio(value: float | None) -> str:
    return f"{(value or 0):.2f}"


def format_eta(seconds: int | float | None) -> str:
    if seconds is None or seconds < 0:
        return "--"
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m"
    if minutes:
        return f"{minutes:d}m {secs:02d}s"
    return f"{secs:d}s"
