from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from uctorrent.app.services.theme_service import ThemeService
from uctorrent.app.ui.add_torrent_dialog import AddTorrentDialog
from uctorrent.app.ui.batch_add_dialog import BatchAddDialog
from uctorrent.app.ui.delegates import ProgressBarDelegate, STATUS_ROLE, StatusBadgeDelegate
from uctorrent.app.ui.details_panel import DetailsPanel
from uctorrent.app.ui.icon_service import ICON_NAMES, IconService
from uctorrent.app.ui.main_window import MainWindow
from uctorrent.app.ui.settings_window import SettingsWindow
from uctorrent.app.ui.torrent_table import TorrentTable
from uctorrent.app.utils.constants import UI_STYLE_PATH
from uctorrent.app.utils.formatters import display_text


def _app():
    return QApplication.instance() or QApplication([])


class FakeConfig:
    def __init__(self):
        self.values = {"app.first_run_legal_notice_accepted": True}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class FakeManager:
    def list_torrents(self):
        return [
            {
                "id": 1,
                "name": "Ubuntu ISO",
                "status": "downloading",
                "progress": 0.42,
                "download_rate": 1024,
                "upload_rate": 128,
                "seeds": 4,
                "peers": 8,
            }
        ]

    def get_torrent_details(self, torrent_id):
        return {
            "id": torrent_id,
            "name": "Ubuntu ISO",
            "status": "downloading",
            "progress": 0.42,
            "total_size": 2048,
            "downloaded": 1024,
            "uploaded": 128,
            "ratio": 0.1,
            "seeds": 4,
            "peers": 8,
            "download_rate": 1024,
            "upload_rate": 128,
            "files": [],
            "trackers": [],
            "peers_detail": [],
            "pieces": [0, 1, 2],
            "logs": [],
        }


class FakeLog:
    def info(self, *_args):
        return None


def test_local_svg_icons_load():
    _app()
    missing = [name for name in ICON_NAMES if IconService.icon(name).isNull()]
    assert missing == []


def test_torrent_table_uses_modern_delegates_and_keeps_selection():
    app = _app()
    table = TorrentTable()
    table.set_torrents(
        [
            {"id": 1, "name": "One", "status": "paused", "progress": 0.1},
            {"id": 2, "name": "Two", "status": "downloading", "progress": 0.7},
        ],
        selected_ids=[1, 2],
    )

    table.set_torrents(
        [
            {"id": 1, "name": "One", "status": "downloading", "progress": 0.2},
            {"id": 2, "name": "Two", "status": "downloading", "progress": 0.8},
        ],
        selected_ids=table.selected_torrent_ids(),
    )

    assert isinstance(table.itemDelegateForColumn(2), ProgressBarDelegate)
    assert isinstance(table.itemDelegateForColumn(3), StatusBadgeDelegate)
    assert set(table.selected_torrent_ids()) == {1, 2}
    app.processEvents()


def test_torrent_table_status_change_highlight_is_theme_safe():
    app = _app()
    service = ThemeService(UI_STYLE_PATH)
    original_palette = app.palette()
    try:
        app.setPalette(service.palette("dark", original_palette))
        dark_table = TorrentTable()
        dark_table.set_torrents([{"id": 1, "name": "One", "status": "paused"}])
        dark_table.set_torrents([{"id": 1, "name": "One", "status": "checking"}])
        assert dark_table.item(0, 0).background().color().lightness() < 170

        app.setPalette(service.palette("light", original_palette))
        light_table = TorrentTable()
        light_table.set_torrents([{"id": 1, "name": "One", "status": "paused"}])
        light_table.set_torrents([{"id": 1, "name": "One", "status": "checking"}])
        assert light_table.item(0, 0).background().color().lightness() < 250
    finally:
        app.setPalette(original_palette)


def test_qt_views_coerce_bytes_to_display_text():
    app = _app()
    binary_hash = b"\x00\xff\x10hash"
    torrent = {
        "id": 9,
        "name": b"Torrent com bytes",
        "status": b"checking",
        "progress": 0.13,
        "total_size": 4096,
        "downloaded": 512,
        "uploaded": 64,
        "ratio": 0.1,
        "seeds": 1,
        "peers": 2,
        "info_hash": binary_hash,
        "magnet_uri": b"magnet:?xt=urn:btih:abc",
        "category": b"Filmes",
        "tags": [b"vr", "legal"],
        "save_path": b"C:/Downloads",
        "files": [{"path": b"pasta/video.mp4", "size": 1024, "progress": 0.5, "priority": 1}],
        "trackers": [{"url": b"https://tracker.local/announce", "status": b"ok", "message": b"ativo", "seeds": 1, "peers": 2}],
        "peers_detail": [{"ip": b"127.0.0.1", "port": 6881, "client": b"lt", "progress": 0.2, "download_rate": 5, "upload_rate": 2}],
        "pieces": [1, 0, 1],
        "logs": [{"created_at": b"2026-06-17", "level": b"INFO", "message": b"ok"}],
    }

    table = TorrentTable()
    selected = []
    table.torrent_selected.connect(selected.append)
    table.set_torrents([torrent])
    table.selectRow(0)
    details = DetailsPanel()
    details.show_torrent(torrent)

    assert table.item(0, 0).text() == "Torrent com bytes"
    assert table.item(0, 3).data(STATUS_ROLE) == "checking"
    assert details.title.text() == "Torrent com bytes"
    assert details.subtitle.text() == display_text(binary_hash)
    assert details.files.topLevelItem(0).text(0) == "pasta/video.mp4"
    assert details.trackers.topLevelItem(0).text(0) == "https://tracker.local/announce"
    assert details.peers.topLevelItem(0).text(2) == "lt"
    assert selected[0]["name"] == b"Torrent com bytes"
    app.processEvents()


def test_desktop_windows_instantiate_offscreen():
    app = _app()
    config = FakeConfig()
    details = DetailsPanel()
    details.show_torrent(FakeManager().get_torrent_details(1))
    batch = BatchAddDialog([{"kind": "magnet", "magnet_uri": "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"}], "C:/Downloads")
    settings = SettingsWindow(config)
    add_torrent = AddTorrentDialog()
    main = MainWindow(FakeManager(), config, FakeLog())
    main.timer.stop()
    main.tray_icon.hide()

    assert details.count() >= 6
    assert batch.save_path.text() == "C:/Downloads"
    assert settings.tabs.count() >= 6
    assert settings.sections.count() >= 6
    assert add_torrent.windowTitle()
    assert main.header.search.placeholderText()
    assert main.header.maximumHeight() == 64
    main.resize(1100, 680)
    main.content_splitter.setSizes([600, 50])
    app.processEvents()
    assert main.content_splitter.sizes()[1] <= 70
    main.close()


def test_details_summary_scrolls_when_panel_is_short():
    app = _app()
    details = DetailsPanel()
    details.show_torrent(FakeManager().get_torrent_details(1))
    details.resize(1000, 120)
    details.show()
    app.processEvents()

    assert details.summary_scroll.verticalScrollBar().maximum() > 0
    details.close()


def test_main_window_applies_theme_without_restart():
    app = _app()
    config = FakeConfig()
    main = MainWindow(FakeManager(), config, FakeLog())
    main.timer.stop()
    main.tray_icon.hide()

    app.uctorrent_base_palette = app.palette()
    config.set("app.theme", "dark")
    main.apply_theme()
    dark_window = app.palette().color(QPalette.Window).lightness()

    config.set("app.theme", "light")
    main.apply_theme()
    light_window = app.palette().color(QPalette.Window).lightness()

    assert dark_window < light_window
    main.close()


def test_main_window_close_hides_to_tray_when_available():
    app = _app()
    config = FakeConfig()
    main = MainWindow(FakeManager(), config, FakeLog())
    main.timer.stop()
    main.tray_icon.hide()
    main.show()
    app.processEvents()

    with patch("uctorrent.app.ui.main_window.QSystemTrayIcon.isSystemTrayAvailable", return_value=True):
        main.close()
    app.processEvents()

    assert not main.isVisible()
    assert main._allow_close is False

    main.show_from_tray()
    app.processEvents()
    assert main.isVisible()
    main._allow_close = True
    main.close()


def test_theme_service_replaces_modern_tokens():
    qss = ThemeService(UI_STYLE_PATH).load("light")
    assert "@surfaceElevated" not in qss
    assert "@shadowBorder" not in qss
    assert "#appHeader" in qss
