from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QPushButton, QVBoxLayout


class SearchWindow(QDialog):
    def __init__(self, search_service, parent=None):
        super().__init__(parent)
        self.search_service = search_service
        self.setWindowTitle("UCtorrent - busca segura")
        self.query = QLineEdit()
        self.query.setPlaceholderText("Buscar em fontes legais configuradas")
        self.results = QListWidget()
        button = QPushButton("Buscar")
        button.clicked.connect(self.search)
        layout = QVBoxLayout(self)
        layout.addWidget(self.query)
        layout.addWidget(button)
        layout.addWidget(self.results)

    def search(self):
        self.results.clear()
        for item in self.search_service.search(self.query.text()):
            self.results.addItem(item.get("name", str(item)))

