from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLabel, QLineEdit, QPushButton


class CreateTorrentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UCtorrent - criar torrent")
        self.source = QLineEdit()
        self.output = QLineEdit()
        self.trackers = QLineEdit()
        self.comment = QLineEdit()
        self.private = QCheckBox("Torrent privado")
        select_source = QPushButton("Selecionar arquivo/pasta")
        select_source.clicked.connect(self._select_source)
        select_output = QPushButton("Selecionar destino")
        select_output.clicked.connect(self._select_output)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Ferramenta basica de criacao de .torrent."))
        layout.addRow("Arquivo ou pasta", self.source)
        layout.addRow("", select_source)
        layout.addRow("Arquivo .torrent destino", self.output)
        layout.addRow("", select_output)
        layout.addRow("Trackers", self.trackers)
        layout.addRow("Comentario", self.comment)
        layout.addRow("", self.private)
        layout.addRow(buttons)

    def _select_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta")
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo")
        if path:
            self.source.setText(path)

    def _select_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Salvar .torrent", "", "Torrent (*.torrent)")
        if path:
            self.output.setText(path if path.endswith(".torrent") else f"{path}.torrent")

    def values(self) -> dict:
        return {
            "source": self.source.text().strip(),
            "output": self.output.text().strip(),
            "trackers": [item.strip() for item in self.trackers.text().split(",") if item.strip()],
            "comment": self.comment.text().strip(),
            "private": self.private.isChecked(),
        }
