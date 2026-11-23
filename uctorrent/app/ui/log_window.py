from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout

from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import LogRepository


class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UCtorrent - logs")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        self.refresh()

    def refresh(self):
        session = get_session()
        try:
            lines = [f"{log.created_at} [{log.level}] {log.scope}: {log.message}" for log in LogRepository(session).list()]
            self.text.setPlainText("\n".join(lines))
        finally:
            session.close()

