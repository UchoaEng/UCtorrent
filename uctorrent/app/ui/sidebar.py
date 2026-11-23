from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from uctorrent.app.ui.icon_service import IconService


class Sidebar(QListWidget):
    filter_changed = Signal(str)

    FILTERS = [
        "Todos",
        "Baixando",
        "Semeando",
        "Finalizados",
        "Pausados",
        "Ativos",
        "Inativos",
        "Com erro",
        "Categorias",
        "Tags",
        "Trackers",
        "RSS",
    ]
    ICONS = {
        "Todos": "torrent",
        "Baixando": "download",
        "Semeando": "upload",
        "Finalizados": "play",
        "Pausados": "pause",
        "Ativos": "activity",
        "Inativos": "queue",
        "Com erro": "warning",
        "Categorias": "category",
        "Tags": "tag",
        "Trackers": "tracker",
        "RSS": "rss",
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setMinimumWidth(176)
        self.setMaximumWidth(248)
        for item in self.FILTERS:
            row = QListWidgetItem(IconService.icon(self.ICONS.get(item, "torrent")), item)
            row.setData(Qt.UserRole, item)
            self.addItem(row)
        self.setCurrentRow(0)
        self.currentItemChanged.connect(self._emit_filter)

    def set_counts(self, counts: dict[str, int]) -> None:
        self.blockSignals(True)
        for index in range(self.count()):
            item = self.item(index)
            base = item.data(Qt.UserRole)
            if base in counts:
                item.setText(f"{base}  {counts[base]}")
            else:
                item.setText(base)
        self.blockSignals(False)

    def _emit_filter(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None = None) -> None:
        if current is not None:
            self.filter_changed.emit(current.data(Qt.UserRole))
