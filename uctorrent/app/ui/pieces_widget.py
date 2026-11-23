from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtWidgets import QWidget


class PiecesWidget(QWidget):
    COLORS = {
        0: QColor("#d1d5db"),
        1: QColor("#22c55e"),
        2: QColor("#f59e0b"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pieces: list[int] = []
        self.piece_size = 10
        self.setMinimumHeight(0)

    def update_pieces(self, pieces: list[int]) -> None:
        self.pieces = pieces
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        if not self.pieces:
            return QSize(320, 80)
        width = max(self.width(), 320)
        per_row = max(width // self.piece_size, 1)
        rows = (len(self.pieces) + per_row - 1) // per_row
        return QSize(width, max(rows * self.piece_size, 80))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().color(QPalette.Base))
        if not self.pieces:
            painter.setPen(self.palette().color(QPalette.PlaceholderText))
            painter.drawText(self.rect(), 0x84, "Sem dados de pieces para este torrent.")
            return
        per_row = max(self.width() // self.piece_size, 1)
        for index, state in enumerate(self.pieces):
            x = (index % per_row) * self.piece_size
            y = (index // per_row) * self.piece_size
            painter.fillRect(x, y, self.piece_size - 1, self.piece_size - 1, self.COLORS.get(int(state), self.COLORS[0]))
