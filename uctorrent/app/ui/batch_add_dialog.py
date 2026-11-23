from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from uctorrent.app.ui.icon_service import IconService


class BatchAddDialog(QDialog):
    def __init__(self, items: list[dict], default_save_path: str = "", parent=None):
        super().__init__(parent)
        self.items = items
        self.setWindowTitle("UCtorrent - adicionar lote")
        self.resize(680, 460)

        self.list = QListWidget()
        for item in items:
            label = item.get("path") or item.get("magnet_uri") or ""
            self.list.addItem(f"{item.get('kind', 'item')}: {label}")

        self.save_path = QLineEdit(default_save_path)
        browse_save_path = QPushButton("Explorar")
        browse_save_path.setIcon(IconService.icon("folder"))
        browse_save_path.clicked.connect(self._browse_save_path)
        save_path_row = QWidget()
        save_path_layout = QHBoxLayout(save_path_row)
        save_path_layout.setContentsMargins(0, 0, 0, 0)
        save_path_layout.addWidget(self.save_path)
        save_path_layout.addWidget(browse_save_path)

        self.category = QLineEdit()
        self.tags = QLineEdit()
        self.paused = QCheckBox("Adicionar pausado")
        self.sequential = QCheckBox("Download sequencial")
        self.first_last = QCheckBox("Baixar primeira e ultima peca primeiro")

        form = QFormLayout()
        form.addRow("Destino do lote", save_path_row)
        form.addRow("Categoria", self.category)
        form.addRow("Tags", self.tags)
        form.addRow("", self.paused)
        form.addRow("", self.sequential)
        form.addRow("", self.first_last)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _browse_save_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino final", self.save_path.text())
        if path:
            self.save_path.setText(path)

    def values(self) -> dict:
        return {
            "items": self.items,
            "save_path": self.save_path.text().strip() or None,
            "category": self.category.text().strip() or None,
            "tags": [tag.strip() for tag in self.tags.text().split(",") if tag.strip()],
            "paused": self.paused.isChecked(),
            "sequential_download": self.sequential.isChecked(),
            "first_last_piece_priority": self.first_last.isChecked(),
        }


def batch_items_from_paths(paths: list[str | Path]) -> list[dict]:
    items = []
    for path in paths:
        file_path = Path(path)
        if file_path.suffix.lower() == ".torrent":
            items.append({"kind": "torrent", "path": str(file_path)})
    return items
