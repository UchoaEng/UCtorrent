from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QListWidget, QVBoxLayout


class RssWindow(QDialog):
    def __init__(self, rss_service, parent=None):
        super().__init__(parent)
        self.rss_service = rss_service
        self.setWindowTitle("UCtorrent - RSS")
        self.name = QLineEdit()
        self.url = QLineEdit()
        self.list = QListWidget()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        buttons.accepted.connect(self.add_feed)
        buttons.rejected.connect(self.reject)
        form = QFormLayout()
        form.addRow("Nome", self.name)
        form.addRow("URL", self.url)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.list)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for feed in self.rss_service.list_feeds():
            self.list.addItem(f"{feed['name']} - {feed['url']}")

    def add_feed(self):
        self.rss_service.add_feed(self.name.text(), self.url.text())
        self.refresh()

