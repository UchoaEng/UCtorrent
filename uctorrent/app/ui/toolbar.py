from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QToolBar

from uctorrent.app.ui.icon_service import IconService


class MainToolBar(QToolBar):
    add_torrent = Signal()
    add_magnet = Signal()
    create_torrent = Signal()
    start = Signal()
    pause = Signal()
    remove = Signal()
    settings = Signal()
    rss = Signal()
    search_changed = Signal(str)

    def __init__(self):
        super().__init__("UCtorrent")
        self.setObjectName("mainToolbar")
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.addAction(IconService.icon("torrent"), "Torrent", self.add_torrent.emit)
        self.addAction(IconService.icon("magnet"), "Magnet", self.add_magnet.emit)
        self.addAction(IconService.icon("folder"), "Criar", self.create_torrent.emit)
        self.addSeparator()
        self.addAction(IconService.icon("play"), "Iniciar", self.start.emit)
        self.addAction(IconService.icon("pause"), "Pausar", self.pause.emit)
        self.addAction(IconService.icon("remove"), "Remover", self.remove.emit)
        self.addSeparator()
        self.addAction(IconService.icon("rss"), "RSS", self.rss.emit)
        self.addAction(IconService.icon("settings"), "Config", self.settings.emit)
