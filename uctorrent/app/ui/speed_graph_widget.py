from __future__ import annotations

from PySide6.QtWidgets import QLabel


class SpeedGraphWidget(QLabel):
    def __init__(self):
        super().__init__("Grafico de velocidade em tempo real")

