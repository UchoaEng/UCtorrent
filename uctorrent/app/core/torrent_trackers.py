from __future__ import annotations


def normalize_trackers(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

