from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette


class ThemeService:
    LIGHT = {
        "text": "#172033",
        "muted": "#526070",
        "window": "#eef2f6",
        "surface": "#ffffff",
        "surface_alt": "#f8fafc",
        "surfaceElevated": "#ffffff",
        "field": "#ffffff",
        "field_alt": "#f6f8fb",
        "line": "#d7dee8",
        "line_soft": "#edf1f5",
        "shadowBorder": "#cfd8e6",
        "button_border": "#c8d2df",
        "hover": "#eef5ff",
        "pressed": "#dbeafe",
        "accent": "#4f8df7",
        "accent_soft": "#dbeafe",
        "accent_border": "#8bb8ff",
        "accent_text": "#12356f",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#0284c7",
        "selection": "#dbeafe",
        "scroll_bg": "#f1f5f9",
        "scroll_handle": "#b8c4d2",
        "scroll_handle_hover": "#8fa1b8",
    }
    DARK = {
        "text": "#e5edf7",
        "muted": "#9fb0c3",
        "window": "#111827",
        "surface": "#1f2937",
        "surface_alt": "#162033",
        "surfaceElevated": "#243044",
        "field": "#111827",
        "field_alt": "#172033",
        "line": "#334155",
        "line_soft": "#263244",
        "shadowBorder": "#415169",
        "button_border": "#475569",
        "hover": "#24334a",
        "pressed": "#1d4ed8",
        "accent": "#60a5fa",
        "accent_soft": "#1e3a5f",
        "accent_border": "#3b82f6",
        "accent_text": "#dbeafe",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#f87171",
        "info": "#38bdf8",
        "selection": "#1e3a5f",
        "scroll_bg": "#172033",
        "scroll_handle": "#475569",
        "scroll_handle_hover": "#64748b",
    }

    def __init__(self, qss_path: Path):
        self.qss_path = qss_path

    def resolved_theme(self, theme: str = "system", system_palette: QPalette | None = None) -> str:
        if theme in {"light", "dark"}:
            return theme
        palette = system_palette or QPalette()
        return "dark" if palette.color(QPalette.Window).lightness() < 128 else "light"

    def colors(self, theme: str = "system", system_palette: QPalette | None = None) -> dict[str, str]:
        return self.DARK if self.resolved_theme(theme, system_palette) == "dark" else self.LIGHT

    def load(self, theme: str = "system", system_palette: QPalette | None = None) -> str:
        if not self.qss_path.exists():
            return ""
        qss = self.qss_path.read_text(encoding="utf-8")
        for key, value in self.colors(theme, system_palette).items():
            qss = qss.replace(f"@{key}", value)
        return qss

    def palette(self, theme: str = "system", system_palette: QPalette | None = None) -> QPalette:
        colors = self.colors(theme, system_palette)
        palette = QPalette(system_palette or QPalette())
        palette.setColor(QPalette.Window, QColor(colors["window"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.Base, QColor(colors["surface"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["surface_alt"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.Highlight, QColor(colors["selection"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["text"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
        return palette
