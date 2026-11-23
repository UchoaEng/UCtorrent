from __future__ import annotations


class NotificationService:
    def notify(self, title: str, message: str) -> None:
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app and hasattr(app, "tray_icon"):
                app.tray_icon.showMessage(title, message)
        except Exception:
            return

