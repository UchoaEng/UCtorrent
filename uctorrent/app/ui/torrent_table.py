from __future__ import annotations

from PySide6.QtCore import QItemSelectionModel, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractItemView, QAbstractScrollArea, QHeaderView, QSizePolicy, QTableWidget, QTableWidgetItem

from uctorrent.app.ui.delegates import PROGRESS_ROLE, STATUS_ROLE, ProgressBarDelegate, StatusBadgeDelegate
from uctorrent.app.ui.icon_service import IconService
from uctorrent.app.utils.constants import TORRENT_STATUSES
from uctorrent.app.utils.formatters import display_text, format_bytes, format_eta, format_ratio, format_speed


class TorrentTable(QTableWidget):
    torrent_selected = Signal(object)

    COLUMNS = [
        "Nome",
        "Tamanho",
        "Progresso",
        "Status",
        "Seeds",
        "Peers",
        "Download",
        "Upload",
        "ETA",
        "Ratio",
        "Categoria",
        "Tags",
        "Prioridade",
        "Destino",
        "Adicionado",
    ]

    def __init__(self):
        super().__init__(0, len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setObjectName("torrentTable")
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnWidth(0, 260)
        self.setColumnWidth(1, 92)
        self.setColumnWidth(2, 90)
        self.setColumnWidth(3, 150)
        self.setColumnWidth(13, 220)
        self.setItemDelegateForColumn(2, ProgressBarDelegate(self))
        self.setItemDelegateForColumn(3, StatusBadgeDelegate(self))
        self._torrents: list[dict] = []
        self._last_status_by_id: dict[int, str] = {}
        self.itemSelectionChanged.connect(self._emit_selection)

    def set_torrents(self, torrents: list[dict], selected_ids: list[int] | None = None) -> None:
        selected_ids = self.selected_torrent_ids() if selected_ids is None else selected_ids
        selected_id_set = {int(item) for item in selected_ids}
        self.blockSignals(True)
        self.setSortingEnabled(False)
        self._torrents = torrents
        self.setRowCount(len(torrents))
        for row, torrent in enumerate(torrents):
            status_key = display_text(torrent.get("status", ""))
            torrent_id = torrent.get("id")
            torrent_id_data = self._item_id_data(torrent_id)
            values = [
                display_text(torrent.get("name", "")),
                format_bytes(torrent.get("total_size", 0)),
                f"{int((torrent.get('progress') or 0) * 100)}%",
                TORRENT_STATUSES.get(status_key, status_key),
                str(torrent.get("seeds", 0)),
                str(torrent.get("peers", 0)),
                format_speed(torrent.get("download_rate", 0)),
                format_speed(torrent.get("upload_rate", 0)),
                format_eta(torrent.get("eta")),
                format_ratio(torrent.get("ratio", 0)),
                display_text(torrent.get("category") or ""),
                ", ".join(display_text(tag) for tag in (torrent.get("tags") or [])),
                str(torrent.get("priority", 0)),
                display_text(torrent.get("save_path") or ""),
                display_text(torrent.get("added_at") or ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(display_text(value))
                item.setData(Qt.UserRole, torrent_id_data)
                if col == 0:
                    item.setIcon(self._icon_for_status(status_key))
                if col == 2:
                    item.setData(PROGRESS_ROLE, float(torrent.get("progress") or 0))
                if col == 3:
                    item.setData(STATUS_ROLE, status_key)
                if torrent_id is not None and self._last_status_by_id.get(int(torrent_id)) not in {None, status_key}:
                    item.setBackground(self._status_change_background())
                self.setItem(row, col, item)
            if torrent.get("id") is not None:
                self._last_status_by_id[int(torrent["id"])] = status_key
        self.setSortingEnabled(True)
        self.clearSelection()
        selection_model = self.selectionModel()
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and int(item.data(Qt.UserRole)) in selected_id_set:
                selection_model.select(self.model().index(row, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.blockSignals(False)
        self._emit_selection()

    def selected_torrent_ids(self) -> list[int]:
        ids = []
        for index in self.selectionModel().selectedRows():
            item = self.item(index.row(), 0)
            if item:
                ids.append(int(item.data(Qt.UserRole)))
        return ids

    def _emit_selection(self) -> None:
        ids = self.selected_torrent_ids()
        if not ids:
            return
        selected = next((torrent for torrent in self._torrents if torrent.get("id") == ids[0]), None)
        if selected:
            self.torrent_selected.emit(selected)

    def torrent_id_at_row(self, row: int) -> int | None:
        item = self.item(row, 0)
        if not item:
            return None
        return int(item.data(Qt.UserRole))

    def _icon_for_status(self, status: str):
        if status in {"downloading", "metadata"}:
            return IconService.icon("download")
        if status == "seeding":
            return IconService.icon("upload")
        if status in {"paused", "queued", "offline"}:
            return IconService.icon("pause")
        if status in {"error", "no_seeds"}:
            return IconService.icon("warning")
        return IconService.icon("torrent")

    def _status_change_background(self) -> QColor:
        color = QColor(self.palette().color(QPalette.Highlight))
        if color.lightness() > 210:
            color = color.darker(105)
        return color

    def _item_id_data(self, torrent_id):
        if torrent_id is None:
            return None
        try:
            return int(torrent_id)
        except (TypeError, ValueError):
            return display_text(torrent_id)
