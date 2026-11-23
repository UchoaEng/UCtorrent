from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from uctorrent.app.ui.icon_service import IconService


class AddTorrentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UCtorrent - adicionar torrent")
        self.torrent_path = QLineEdit()
        browse = QPushButton("Selecionar")
        browse.setIcon(IconService.icon("torrent"))
        browse.clicked.connect(self._browse_torrent)
        self.save_path = QLineEdit()
        self.save_path.setPlaceholderText("Pasta onde os arquivos baixados ficarao")
        browse_save_path = QPushButton("Selecionar pasta")
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("Arquivo .torrent", self.torrent_path)
        layout.addRow("", browse)
        layout.addRow("Destino final", save_path_row)
        layout.addRow("Categoria", self.category)
        layout.addRow("Tags", self.tags)
        layout.addRow("", self.paused)
        layout.addRow(buttons)

    def _browse_torrent(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar .torrent", "", "Torrent (*.torrent)")
        if path:
            self.torrent_path.setText(path)

    def _browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino final")
        if path:
            self.save_path.setText(path)

    def values(self) -> dict:
        return {
            "torrent_path": self.torrent_path.text().strip(),
            "save_path": self.save_path.text().strip() or None,
            "category": self.category.text().strip() or None,
            "tags": [tag.strip() for tag in self.tags.text().split(",") if tag.strip()],
            "paused": self.paused.isChecked(),
        }
