from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from uctorrent.app.ui.icon_service import IconService
from uctorrent.app.ui.pieces_widget import PiecesWidget
from uctorrent.app.utils.constants import TORRENT_STATUSES
from uctorrent.app.utils.formatters import display_text, format_bytes, format_ratio, format_speed


class DetailsPanel(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("detailsPanel")
        self.setMinimumWidth(0)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        summary_page = QWidget()
        summary_page.setObjectName("detailsSummaryPage")
        summary_page.setMinimumWidth(0)
        summary_page.setMinimumHeight(0)
        summary_page.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        layout = QVBoxLayout(summary_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.summary_scroll = QScrollArea()
        self.summary_scroll.setObjectName("detailsSummaryScroll")
        self.summary_scroll.setFrameShape(QScrollArea.NoFrame)
        self.summary_scroll.setWidgetResizable(True)
        self.summary_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.summary_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_scroll.setMinimumHeight(0)
        self.summary_scroll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.summary_content = QWidget()
        self.summary_content.setObjectName("detailsSummaryContent")
        self.summary_content.setMinimumHeight(0)
        self.summary_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.summary_content_layout = QVBoxLayout(self.summary_content)
        self.summary_content_layout.setContentsMargins(14, 12, 14, 12)
        self.summary_content_layout.setSpacing(10)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("Nenhum torrent selecionado")
        self.title.setObjectName("detailsTitle")
        self.title.setMinimumHeight(24)
        self.title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("detailsSubtitle")
        self.subtitle.setMinimumHeight(18)
        self.subtitle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        self.summary_content_layout.addLayout(header)
        self.summary_grid = QGridLayout()
        self.summary_grid.setHorizontalSpacing(14)
        self.summary_grid.setVerticalSpacing(8)
        self.summary_fields: dict[str, QLabel] = {}
        for index, key in enumerate(
            [
                "Status",
                "Progresso",
                "Tamanho",
                "Baixado",
                "Enviado",
                "Ratio",
                "Seeds",
                "Peers",
                "Disponibilidade",
                "Download",
                "Upload",
                "Categoria",
                "Tags",
                "Destino",
            ]
        ):
            label = QLabel(key)
            label.setObjectName("summaryLabel")
            label.setMinimumHeight(20)
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            value = QLabel("")
            value.setObjectName("summaryValue")
            value.setMinimumHeight(20)
            value.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row = index // 2
            col = (index % 2) * 2
            self.summary_grid.addWidget(label, row, col)
            self.summary_grid.addWidget(value, row, col + 1)
            self.summary_fields[key] = value
        self.summary_content_layout.addLayout(self.summary_grid)
        self.summary = QPlainTextEdit("")
        self.summary.setObjectName("detailsRawSummary")
        self.summary.setReadOnly(True)
        self.summary.setFrameShape(QPlainTextEdit.NoFrame)
        self.summary.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.summary.setMinimumHeight(86)
        self.summary.setMaximumHeight(86)
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapAnywhere)
        self.summary.document().setDefaultTextOption(text_option)
        self.summary_content_layout.addWidget(self.summary)
        self.summary_scroll.setWidget(self.summary_content)
        layout.addWidget(self.summary_scroll)
        self.addTab(summary_page, IconService.icon("torrent"), "Resumo")

        self.files = QTreeWidget()
        self.files.setHeaderLabels(["Nome", "Tamanho", "Progresso", "Prioridade", "Caminho"])
        self._constrain_tree(self.files)
        self.addTab(self.files, IconService.icon("folder"), "Arquivos")

        self.trackers = QTreeWidget()
        self.trackers.setHeaderLabels(["URL", "Status", "Mensagem", "Seeds", "Peers"])
        self._constrain_tree(self.trackers)
        self.addTab(self.trackers, IconService.icon("tracker"), "Trackers")

        self.peers = QTreeWidget()
        self.peers.setHeaderLabels(["IP", "Porta", "Cliente", "Progresso", "Download", "Upload"])
        self._constrain_tree(self.peers)
        self.addTab(self.peers, IconService.icon("activity"), "Peers")

        self.pieces = PiecesWidget()
        self.addTab(self.pieces, IconService.icon("queue"), "Pieces")

        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.logs.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logs.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.logs.setMinimumWidth(0)
        self.logs.setMinimumHeight(0)
        self.logs.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.addTab(self.logs, IconService.icon("warning"), "Logs")

    def _constrain_tree(self, tree: QTreeWidget) -> None:
        tree.setMinimumWidth(0)
        tree.setMinimumHeight(0)
        tree.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        tree.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)

    def show_torrent(self, torrent: dict) -> None:
        status_key = display_text(torrent.get("status", ""))
        status = TORRENT_STATUSES.get(status_key, status_key)
        self.title.setText(display_text(torrent.get("name", "")) or "Torrent sem nome")
        self.subtitle.setText(display_text(torrent.get("info_hash") or torrent.get("magnet_uri") or ""))
        field_values = {
            "Status": status,
            "Progresso": f"{int((torrent.get('progress') or 0) * 100)}%",
            "Tamanho": format_bytes(torrent.get("total_size", 0)),
            "Baixado": format_bytes(torrent.get("downloaded", 0)),
            "Enviado": format_bytes(torrent.get("uploaded", 0)),
            "Ratio": format_ratio(torrent.get("ratio", 0)),
            "Seeds": str(torrent.get("seeds", 0)),
            "Peers": str(torrent.get("peers", 0)),
            "Disponibilidade": f"{float(torrent.get('availability') or 0):.2f}",
            "Download": format_speed(torrent.get("download_rate", 0)),
            "Upload": format_speed(torrent.get("upload_rate", 0)),
            "Categoria": display_text(torrent.get("category") or "-"),
            "Tags": ", ".join(display_text(tag) for tag in (torrent.get("tags") or [])) or "-",
            "Destino": display_text(torrent.get("save_path") or "-"),
        }
        for key, value in field_values.items():
            self.summary_fields[key].setText(display_text(value))
        self.summary.setPlainText(
            "\n".join(
                [
                    f"Hash: {display_text(torrent.get('info_hash') or '')}",
                    f"Magnet: {display_text(torrent.get('magnet_uri') or '')}",
                    f"Erro: {display_text(torrent.get('error') or '')}",
                ]
            )
        )
        self._show_files(torrent.get("files", []))
        self._show_trackers(torrent.get("trackers", []))
        self._show_peers(torrent.get("peers_detail", []))
        self.pieces.update_pieces(torrent.get("pieces", []))
        self._show_logs(torrent.get("logs", []))
        self._update_summary_scroll_height()

    def _update_summary_scroll_height(self) -> None:
        self.summary_content.setMinimumHeight(self.summary_content_layout.sizeHint().height())

    def _show_files(self, files: list[dict]) -> None:
        self.files.clear()
        for item in files:
            row = QTreeWidgetItem(
                [
                    display_text(item.get("path", "")),
                    format_bytes(item.get("size", 0)),
                    f"{int((item.get('progress') or 0) * 100)}%",
                    str(item.get("priority", "")),
                    display_text(item.get("path", "")),
                ]
            )
            self.files.addTopLevelItem(row)

    def _show_trackers(self, trackers: list[dict]) -> None:
        self.trackers.clear()
        for item in trackers:
            row = QTreeWidgetItem(
                [
                    display_text(item.get("url", "")),
                    display_text(item.get("status") or ""),
                    display_text(item.get("message") or ""),
                    str(item.get("seeds", 0)),
                    str(item.get("peers", 0)),
                ]
            )
            self.trackers.addTopLevelItem(row)

    def _show_peers(self, peers: list[dict]) -> None:
        self.peers.clear()
        for item in peers:
            row = QTreeWidgetItem(
                [
                    display_text(item.get("ip", "")),
                    str(item.get("port", 0)),
                    display_text(item.get("client") or ""),
                    f"{int((item.get('progress') or 0) * 100)}%",
                    format_speed(item.get("download_rate", 0)),
                    format_speed(item.get("upload_rate", 0)),
                ]
            )
            self.peers.addTopLevelItem(row)

    def _show_logs(self, logs: list[dict]) -> None:
        lines = [
            (
                f"{display_text(item.get('created_at', ''))} "
                f"[{display_text(item.get('level', ''))}] "
                f"{display_text(item.get('message', ''))}"
            )
            for item in logs
        ]
        self.logs.setPlainText("\n".join(lines) if lines else "Nenhum evento registrado para este torrent.")
