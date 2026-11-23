from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMainWindow, QMenu, QSplitter, QStatusBar, QSystemTrayIcon, QWidget, QVBoxLayout

from uctorrent.app.core.torrent_filters import STATUS_FILTERS, filter_torrents
from uctorrent.app.core.torrent_creator import TorrentCreator
from uctorrent.app.core.torrent_statistics import aggregate_speeds
from uctorrent.app.services.rss_service import RssService
from uctorrent.app.services.search_service import SearchService
from uctorrent.app.services.theme_service import ThemeService
from uctorrent.app.ui.add_magnet_dialog import AddMagnetDialog
from uctorrent.app.ui.add_torrent_dialog import AddTorrentDialog
from uctorrent.app.ui.batch_add_dialog import BatchAddDialog, batch_items_from_paths
from uctorrent.app.ui.create_torrent_dialog import CreateTorrentDialog
from uctorrent.app.ui.details_panel import DetailsPanel
from uctorrent.app.ui.dialogs import confirm, show_error, show_legal_notice
from uctorrent.app.ui.icon_service import IconService
from uctorrent.app.ui.modern_widgets import CommandHeader, DropOverlay, ToastManager
from uctorrent.app.ui.rss_window import RssWindow
from uctorrent.app.ui.search_window import SearchWindow
from uctorrent.app.ui.settings_window import SettingsWindow
from uctorrent.app.ui.sidebar import Sidebar
from uctorrent.app.ui.toolbar import MainToolBar
from uctorrent.app.ui.torrent_table import TorrentTable
from uctorrent.app.ui.tray_icon import TrayIcon
from uctorrent.app.utils.constants import APP_ICON_PATH, APP_NAME, UI_STYLE_PATH
from uctorrent.app.utils.formatters import display_text, format_speed
from uctorrent.app.utils.magnet_utils import extract_magnets, extract_magnets_from_file


class MainWindow(QMainWindow):
    def __init__(self, manager, config_service, log_service):
        super().__init__()
        self.manager = manager
        self.config_service = config_service
        self.log_service = log_service
        self.search_text = ""
        self.sidebar_filter = "Todos"
        self.selected_torrent_id: int | None = None
        self.selected_torrent_ids: set[int] = set()
        self._allow_close = False
        self._tray_close_hint_shown = False
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1280, 780)
        self.setMinimumSize(880, 560)
        self.setAcceptDrops(True)

        self.toolbar = MainToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.add_torrent.connect(self.add_torrent)
        self.toolbar.add_magnet.connect(self.add_magnet)
        self.toolbar.create_torrent.connect(self.create_torrent)
        self.toolbar.start.connect(self.resume_selected)
        self.toolbar.pause.connect(self.pause_selected)
        self.toolbar.remove.connect(self.remove_selected)
        self.toolbar.settings.connect(self.show_settings)
        self.toolbar.rss.connect(self.show_rss)
        self.toolbar.search_changed.connect(self.set_search)

        self.header = CommandHeader()
        self.header.search_changed.connect(self.set_search)
        self.sidebar = Sidebar()
        self.sidebar.filter_changed.connect(self.set_sidebar_filter)
        self.table = TorrentTable()
        self.details = DetailsPanel()
        self.table.torrent_selected.connect(self.show_torrent_details)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        vertical = QSplitter()
        vertical.setObjectName("contentSplitter")
        vertical.setOrientation(Qt.Vertical)
        vertical.addWidget(self.table)
        vertical.addWidget(self.details)
        vertical.setChildrenCollapsible(True)
        vertical.setCollapsible(0, False)
        vertical.setCollapsible(1, True)
        vertical.setStretchFactor(0, 1)
        vertical.setStretchFactor(1, 0)
        vertical.setSizes([500, 230])
        self.content_splitter = vertical

        splitter = QSplitter()
        splitter.setObjectName("mainSplitter")
        splitter.addWidget(self.sidebar)
        splitter.addWidget(vertical)
        splitter.setSizes([180, 1100])

        central = QWidget()
        central.setObjectName("mainSurface")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(splitter)
        self.setCentralWidget(central)
        self.drop_overlay = DropOverlay(central)
        self.toast = ToastManager(central)
        self.setStatusBar(QStatusBar())
        self.tray_icon = TrayIcon(self)
        QApplication.instance().tray_icon = self.tray_icon
        self.tray_icon.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()
        self._maybe_show_legal_notice()

    def closeEvent(self, event) -> None:
        if self._allow_close or not QSystemTrayIcon.isSystemTrayAvailable():
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
            event.accept()
            return
        event.ignore()
        self.hide()
        if not self._tray_close_hint_shown:
            self.tray_icon.showMessage(
                APP_NAME,
                "UCtorrent continua em segundo plano. Use a bandeja para abrir ou sair.",
                QSystemTrayIcon.Information,
                3500,
            )
            self._tray_close_hint_shown = True

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_application(self) -> None:
        self._allow_close = True
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        QApplication.quit()

    def apply_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        base_palette = getattr(app, "uctorrent_base_palette", None) or app.palette()
        theme_name = self.config_service.get("app.theme", "system")
        theme_service = ThemeService(UI_STYLE_PATH)
        app.setPalette(theme_service.palette(theme_name, base_palette))
        app.setStyleSheet(theme_service.load(theme_name, base_palette))
        self.table.viewport().update()
        self.details.update()

    def _maybe_show_legal_notice(self) -> None:
        if not self.config_service.get("app.first_run_legal_notice_accepted", False):
            if show_legal_notice(self):
                self.config_service.set("app.first_run_legal_notice_accepted", True)
            else:
                self._allow_close = True
                self.close()

    def dragEnterEvent(self, event) -> None:
        if self._mime_has_supported_drop(event.mimeData()):
            event.acceptProposedAction()
            self.drop_overlay.resize_to_parent()
            self.drop_overlay.show()
            self.drop_overlay.raise_()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._mime_has_supported_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        self.drop_overlay.hide()
        items = self._items_from_mime_data(event.mimeData())
        if len(items) > 1:
            added, errors = self._confirm_and_add_batch(items)
        else:
            added, errors = self._add_batch_items(items)
        if added:
            self.refresh()
            self.statusBar().showMessage(f"{added} item(ns) adicionados por arrastar e soltar.")
            self.toast.show_message(f"{added} item(ns) adicionados")
            event.acceptProposedAction()
        elif errors:
            show_error(self, "UCtorrent", "\n".join(errors[:5]))
            event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.drop_overlay.hide()
        super().dragLeaveEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "drop_overlay"):
            self.drop_overlay.resize_to_parent()
        if hasattr(self, "toast") and self.toast.isVisible():
            self.toast.move((self.centralWidget().width() - self.toast.width()) // 2, 18)

    def _mime_has_supported_drop(self, mime_data) -> bool:
        if mime_data.hasText() and extract_magnets(mime_data.text()):
            return True
        for url in mime_data.urls() if mime_data.hasUrls() else []:
            if url.scheme().lower() == "magnet":
                return True
            if url.isLocalFile():
                suffix = Path(url.toLocalFile()).suffix.lower()
                if suffix in {".torrent", ".magnet", ".txt", ".url"}:
                    return True
        return False

    def _items_from_mime_data(self, mime_data) -> list[dict]:
        items: list[dict] = []
        magnets = extract_magnets(mime_data.text()) if mime_data.hasText() else []
        files = []
        for url in mime_data.urls() if mime_data.hasUrls() else []:
            if url.scheme().lower() == "magnet":
                magnets.extend(extract_magnets(url.toString()))
            elif url.isLocalFile():
                files.append(Path(url.toLocalFile()))
        for file_path in files:
            if file_path.suffix.lower() == ".torrent":
                items.append({"kind": "torrent", "path": str(file_path)})
            else:
                magnets.extend(extract_magnets_from_file(file_path))
        seen = set()
        for magnet in magnets:
            if magnet in seen:
                continue
            seen.add(magnet)
            items.append({"kind": "magnet", "magnet_uri": magnet})
        return items

    def _confirm_and_add_batch(self, items: list[dict]) -> tuple[int, list[str]]:
        dialog = BatchAddDialog(items, self.config_service.get("downloads.completed_path", ""), self)
        if not dialog.exec():
            return 0, []
        return self._add_batch_items(**dialog.values())

    def _add_batch_items(
        self,
        items: list[dict],
        save_path: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        paused: bool | None = None,
        sequential_download: bool = False,
        first_last_piece_priority: bool = False,
    ) -> tuple[int, list[str]]:
        added = 0
        errors: list[str] = []
        paused = bool(self.config_service.get("downloads.add_paused_by_default", False)) if paused is None else paused
        tags = tags or []
        for item in items:
            try:
                if item.get("kind") == "torrent":
                    self.manager.add_torrent_file(
                        item["path"],
                        save_path=save_path,
                        category=category,
                        tags=tags,
                        paused=paused,
                        sequential_download=sequential_download,
                        first_last_piece_priority=first_last_piece_priority,
                    )
                    self.log_service.info("ui", f"Torrent adicionado em lote: {item['path']}")
                else:
                    self.manager.add_magnet(
                        item["magnet_uri"],
                        save_path=save_path,
                        category=category,
                        tags=tags,
                        paused=paused,
                        sequential_download=sequential_download,
                        first_last_piece_priority=first_last_piece_priority,
                    )
                    self.log_service.info("ui", "Magnet adicionado em lote.")
                added += 1
            except Exception as exc:
                label = item.get("path") or item.get("magnet_uri") or "item"
                errors.append(f"{label}: {exc}")
        return added, errors

    def set_search(self, text: str) -> None:
        self.search_text = text
        self.refresh()

    def set_sidebar_filter(self, text: str) -> None:
        self.sidebar_filter = text
        self.refresh()

    def refresh(self) -> None:
        try:
            current_ids = set(self.table.selected_torrent_ids())
            if current_ids:
                self.selected_torrent_ids = current_ids
            torrents = self.manager.list_torrents()
            self.sidebar.set_counts(self._sidebar_counts(torrents))
            status = STATUS_FILTERS.get(self.sidebar_filter)
            visible = filter_torrents(torrents, text=self.search_text, status=status)
            visible_ids = {int(item["id"]) for item in visible if item.get("id") is not None}
            selected = [item for item in self.selected_torrent_ids if item in visible_ids]
            self.table.set_torrents(visible, selected_ids=selected)
            speeds = aggregate_speeds(torrents)
            self.header.update_metrics(speeds["download_rate"], speeds["upload_rate"], speeds["active"])
            self.statusBar().showMessage(
                f"Download global: {format_speed(speeds['download_rate'])} | "
                f"Upload global: {format_speed(speeds['upload_rate'])} | "
                f"Ativos: {speeds['active']}"
            )
        except Exception as exc:
            self.statusBar().showMessage(f"Erro ao atualizar: {exc}")

    def _sidebar_counts(self, torrents: list[dict]) -> dict[str, int]:
        counts = {"Todos": len(torrents)}
        for label, status in STATUS_FILTERS.items():
            counts[label] = len(filter_torrents(torrents, status=status))
        return counts

    def show_torrent_details(self, torrent: dict) -> None:
        torrent_id = torrent.get("id")
        if not torrent_id:
            return
        self.selected_torrent_id = int(torrent_id)
        self.selected_torrent_ids = set(self.table.selected_torrent_ids())
        try:
            self.details.show_torrent(self.manager.get_torrent_details(self.selected_torrent_id))
        except Exception as exc:
            self.statusBar().showMessage(f"Erro ao carregar detalhes: {exc}")

    def add_torrent(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar .torrent", "", "Torrent (*.torrent)")
        if len(paths) > 1:
            added, errors = self._confirm_and_add_batch(batch_items_from_paths(paths))
            if added:
                self.statusBar().showMessage(f"{added} torrent(s) adicionados ao lote.")
                self.refresh()
            if errors:
                show_error(self, "UCtorrent", "\n".join(errors[:5]))
            return
        if len(paths) == 1:
            dialog = AddTorrentDialog(self)
            dialog.torrent_path.setText(paths[0])
        else:
            return
        if dialog.exec():
            try:
                self.manager.add_torrent_file(**dialog.values())
                self.log_service.info("ui", "Torrent adicionado pela interface.")
                self.refresh()
            except Exception as exc:
                show_error(self, "UCtorrent", str(exc))

    def add_magnet(self) -> None:
        dialog = AddMagnetDialog(self)
        if dialog.exec():
            try:
                values = dialog.values()
                magnets = extract_magnets(values["magnet_uri"])
                if len(magnets) > 1:
                    items = [{"kind": "magnet", "magnet_uri": magnet} for magnet in magnets]
                    added, errors = self._confirm_and_add_batch(items)
                    if errors:
                        show_error(self, "UCtorrent", "\n".join(errors[:5]))
                    if added:
                        self.statusBar().showMessage(f"{added} magnet(s) adicionados ao lote.")
                else:
                    self.manager.add_magnet(**values)
                self.log_service.info("ui", "Magnet adicionado pela interface.")
                self.refresh()
            except Exception as exc:
                show_error(self, "UCtorrent", str(exc))

    def create_torrent(self) -> None:
        dialog = CreateTorrentDialog(self)
        if dialog.exec():
            values = dialog.values()
            try:
                TorrentCreator().create(
                    Path(values["source"]),
                    Path(values["output"]),
                    values["trackers"],
                    values["comment"],
                    values["private"],
                )
                self.log_service.info("ui", f"Arquivo .torrent criado em {values['output']}.")
                self.statusBar().showMessage(f"Arquivo .torrent criado em {values['output']}")
            except Exception as exc:
                show_error(self, "UCtorrent", str(exc))

    def pause_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.pause(torrent_id)
        self.refresh()

    def resume_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.resume(torrent_id)
        self.refresh()

    def force_start_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.force_start(torrent_id)
        self.refresh()

    def recheck_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.recheck(torrent_id)
        self.refresh()

    def reannounce_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.reannounce(torrent_id)
        self.refresh()

    def recover_sources_selected(self) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.recover_sources(torrent_id)
        self.refresh()
        self.statusBar().showMessage("Tentativa de recuperar fontes acionada para os torrents selecionados.")
        self.toast.show_message("Recuperacao de fontes acionada")

    def remove_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if ids and confirm(self, "UCtorrent", "Remover torrents selecionados da lista?"):
            for torrent_id in ids:
                self.manager.remove(torrent_id)
            self.refresh()

    def remove_selected_with_files(self) -> None:
        ids = self.table.selected_torrent_ids()
        if ids and confirm(self, "UCtorrent", "Remover torrents selecionados e apagar arquivos baixados?"):
            for torrent_id in ids:
                self.manager.remove(torrent_id, delete_files=True)
            self.refresh()

    def set_location_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if not ids:
            return
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino", self.config_service.get("downloads.completed_path", ""))
        if path:
            for torrent_id in ids:
                self.manager.set_location(torrent_id, path)
            self.refresh()

    def rename_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if len(ids) != 1:
            return
        torrent = self._first_selected_torrent()
        name, ok = QInputDialog.getText(self, "UCtorrent", "Novo nome", text=display_text((torrent or {}).get("name", "")))
        if ok and name.strip():
            self.manager.rename(ids[0], name.strip())
            self.refresh()

    def set_limits_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if not ids:
            return
        download, ok = QInputDialog.getInt(self, "UCtorrent", "Limite download B/s (0 = ilimitado)", 0, 0)
        if not ok:
            return
        upload, ok = QInputDialog.getInt(self, "UCtorrent", "Limite upload B/s (0 = ilimitado)", 0, 0)
        if not ok:
            return
        for torrent_id in ids:
            self.manager.set_torrent_limits(torrent_id, download, upload)
        self.refresh()

    def set_sequential_selected(self, enabled: bool) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.set_sequential_download(torrent_id, enabled)
        self.refresh()

    def set_first_last_selected(self, enabled: bool) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.set_first_last_piece_priority(torrent_id, enabled)
        self.refresh()

    def queue_selected(self, action: str) -> None:
        for torrent_id in self.table.selected_torrent_ids():
            self.manager.queue_action(torrent_id, action)
        self.refresh()

    def set_category_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if not ids:
            return
        category, ok = QInputDialog.getText(self, "UCtorrent", "Categoria")
        if ok:
            for torrent_id in ids:
                self.manager.set_category(torrent_id, category.strip() or None)
            self.refresh()

    def set_tags_selected(self) -> None:
        ids = self.table.selected_torrent_ids()
        if not ids:
            return
        tags, ok = QInputDialog.getText(self, "UCtorrent", "Tags separadas por virgula")
        if ok:
            parsed_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            for torrent_id in ids:
                self.manager.set_tags(torrent_id, parsed_tags)
            self.refresh()

    def copy_selected_hash(self) -> None:
        hashes = []
        for torrent_id in self.table.selected_torrent_ids():
            torrent = self.manager.get_torrent_details(torrent_id)
            if torrent.get("info_hash"):
                hashes.append(display_text(torrent["info_hash"]))
        if hashes:
            QApplication.clipboard().setText("\n".join(hashes))

    def copy_selected_magnet(self) -> None:
        magnets = []
        for torrent_id in self.table.selected_torrent_ids():
            torrent = self.manager.get_torrent_details(torrent_id)
            if torrent.get("magnet_uri"):
                magnets.append(display_text(torrent["magnet_uri"]))
        if magnets:
            QApplication.clipboard().setText("\n".join(magnets))

    def open_selected_folder(self) -> None:
        torrent = self._first_selected_torrent()
        if torrent and torrent.get("save_path"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(display_text(torrent["save_path"])))

    def _first_selected_torrent(self) -> dict | None:
        ids = self.table.selected_torrent_ids()
        if not ids:
            return None
        try:
            return self.manager.get_torrent_details(ids[0])
        except Exception:
            return None

    def show_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            torrent_id = self.table.torrent_id_at_row(row)
            if torrent_id not in self.table.selected_torrent_ids():
                self.table.clearSelection()
                self.table.selectRow(row)
                self.selected_torrent_ids = set(self.table.selected_torrent_ids())
        if not self.table.selected_torrent_ids():
            return
        single = len(self.table.selected_torrent_ids()) == 1
        menu = QMenu(self)
        menu.addAction(IconService.icon("play"), "Iniciar", self.resume_selected)
        menu.addAction(IconService.icon("pause"), "Pausar", self.pause_selected)
        menu.addAction(IconService.icon("play"), "Forcar inicio", self.force_start_selected)
        menu.addSeparator()
        menu.addAction(IconService.icon("refresh"), "Reverificar", self.recheck_selected)
        menu.addAction(IconService.icon("tracker"), "Reanunciar", self.reannounce_selected)
        menu.addAction(IconService.icon("recover"), "Tentar encontrar fontes", self.recover_sources_selected)
        menu.addSeparator()
        menu.addAction(IconService.icon("queue"), "Prioridade maxima", lambda: self.queue_selected("top"))
        menu.addAction(IconService.icon("queue"), "Subir na fila", lambda: self.queue_selected("up"))
        menu.addAction(IconService.icon("queue"), "Descer na fila", lambda: self.queue_selected("down"))
        menu.addAction(IconService.icon("queue"), "Prioridade minima", lambda: self.queue_selected("bottom"))
        menu.addSeparator()
        menu.addAction(IconService.icon("category"), "Definir categoria", self.set_category_selected)
        menu.addAction(IconService.icon("tag"), "Definir tags", self.set_tags_selected)
        menu.addAction(IconService.icon("folder"), "Definir pasta de destino", self.set_location_selected)
        if single:
            menu.addAction(IconService.icon("torrent"), "Renomear", self.rename_selected)
        menu.addAction(IconService.icon("activity"), "Definir limites de velocidade", self.set_limits_selected)
        menu.addSeparator()
        menu.addAction(IconService.icon("download"), "Ativar download sequencial", lambda: self.set_sequential_selected(True))
        menu.addAction(IconService.icon("pause"), "Desativar download sequencial", lambda: self.set_sequential_selected(False))
        menu.addAction(IconService.icon("queue"), "Ativar primeira/ultima peca", lambda: self.set_first_last_selected(True))
        menu.addAction(IconService.icon("queue"), "Desativar primeira/ultima peca", lambda: self.set_first_last_selected(False))
        menu.addSeparator()
        menu.addAction(IconService.icon("magnet"), "Copiar magnet", self.copy_selected_magnet)
        menu.addAction(IconService.icon("torrent"), "Copiar hash", self.copy_selected_hash)
        menu.addAction(IconService.icon("folder"), "Abrir pasta de destino", self.open_selected_folder)
        menu.addSeparator()
        menu.addAction(IconService.icon("remove"), "Remover da lista", self.remove_selected)
        menu.addAction(IconService.icon("warning"), "Remover e apagar arquivos", self.remove_selected_with_files)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def show_settings(self) -> None:
        previous_theme = self.config_service.get("app.theme", "system")
        dialog = SettingsWindow(self.config_service, self)
        if dialog.exec():
            current_theme = self.config_service.get("app.theme", "system")
            if current_theme != previous_theme:
                self.apply_theme()
                self.toast.show_message("Tema aplicado")

    def show_rss(self) -> None:
        RssWindow(RssService(), self).exec()

    def show_search(self) -> None:
        SearchWindow(SearchService(), self).exec()
