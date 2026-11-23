from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text

from uctorrent.app.core.event_bus import EventBus
from uctorrent.app.core.torrent_manager import TorrentManager
from uctorrent.app.core.torrent_session import TorrentSession
from uctorrent.app.database.db import get_session, init_database
from uctorrent.app.database.migrations import migrate_existing_database
from uctorrent.app.database.repositories import TorrentRepository


class BatchEngine:
    def __init__(self):
        self.calls = []

    def has_handle(self, info_hash):
        return True

    def status(self, info_hash):
        return {}

    def pause(self, info_hash):
        self.calls.append(("pause", info_hash))

    def resume(self, info_hash):
        self.calls.append(("resume", info_hash))

    def force_start(self, info_hash):
        self.calls.append(("force_start", info_hash))

    def recheck(self, info_hash):
        self.calls.append(("recheck", info_hash))

    def reannounce(self, info_hash):
        self.calls.append(("reannounce", info_hash))

    def remove(self, info_hash, delete_files=False):
        self.calls.append(("remove", info_hash, delete_files))

    def move_storage(self, info_hash, path):
        self.calls.append(("move_storage", info_hash, str(path)))

    def set_torrent_limits(self, info_hash, download_limit=None, upload_limit=None):
        self.calls.append(("limits", info_hash, download_limit, upload_limit))

    def set_sequential_download(self, info_hash, enabled):
        self.calls.append(("sequential", info_hash, enabled))

    def set_first_last_piece_priority(self, info_hash, enabled):
        self.calls.append(("first_last", info_hash, enabled))

    def queue_top(self, info_hash):
        self.calls.append(("queue_top", info_hash))


def setup_function():
    init_database("sqlite:///:memory:")


def _create_torrent(name="One", info_hash="one"):
    session = get_session()
    try:
        torrent = TorrentRepository(session).create(name=name, info_hash=info_hash, status="paused")
        session.commit()
        return torrent.id
    finally:
        session.close()


def test_batch_manager_supports_success_failure_and_events(tmp_path):
    torrent_id = _create_torrent()
    bus = EventBus()
    manager = TorrentManager({}, events=bus)
    engine = BatchEngine()
    manager.engine = engine

    result = manager.batch([torrent_id, 999], "set_location", {"save_path": str(tmp_path)})

    assert result["ok"] is False
    assert result["results"][0]["save_path"] == str(tmp_path)
    assert result["failed"][0]["id"] == 999
    assert ("move_storage", "one", str(tmp_path)) in engine.calls
    assert any(item["event"] == "torrent_updated" for item in bus.since(0))


def test_batch_rejects_unknown_action():
    manager = TorrentManager({}, events=EventBus())

    try:
        manager.batch([1], "dangerous")
    except ValueError as exc:
        assert "nao permitida" in str(exc)
    else:
        raise AssertionError("ValueError esperado")


def test_migration_adds_qbt_compat_columns(tmp_path):
    db_path = tmp_path / "old.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE torrents (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    migrate_existing_database(engine)

    with engine.connect() as connection:
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(torrents)"))}
    assert "download_limit" in columns
    assert "first_last_piece_priority" in columns
    assert "auto_tmm" in columns


class FakePeer:
    ip = ("127.0.0.1", 6881)
    client = "client"
    progress = 0.5
    down_speed = 10
    up_speed = 5
    flags = "I"


class FakeHandle:
    def __init__(self):
        self.calls = []

    def get_peer_info(self):
        return [FakePeer()]

    def move_storage(self, path):
        self.calls.append(("move_storage", path))

    def set_download_limit(self, value):
        self.calls.append(("download", value))

    def set_upload_limit(self, value):
        self.calls.append(("upload", value))

    def set_sequential_download(self, enabled):
        self.calls.append(("sequential", enabled))


def test_torrent_session_fake_handle_actions():
    session = TorrentSession.__new__(TorrentSession)
    handle = FakeHandle()
    session.handles = {"abc": handle}

    assert session.peers("abc")[0]["ip"] == "127.0.0.1"
    session.move_storage("abc", Path("C:/Downloads"))
    session.set_torrent_limits("abc", 100, 200)
    session.set_sequential_download("abc", True)

    assert ("move_storage", "C:\\Downloads") in handle.calls or ("move_storage", "C:/Downloads") in handle.calls
    assert ("download", 100) in handle.calls
    assert ("upload", 200) in handle.calls
    assert ("sequential", True) in handle.calls


def test_batch_add_dialog_values():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from uctorrent.app.ui.batch_add_dialog import BatchAddDialog

    app = QApplication.instance() or QApplication([])
    dialog = BatchAddDialog([{"kind": "magnet", "magnet_uri": "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"}], "C:/Downloads")
    dialog.category.setText("Linux")
    dialog.tags.setText("iso, legal")
    dialog.paused.setChecked(True)
    dialog.sequential.setChecked(True)

    values = dialog.values()

    assert values["save_path"] == "C:/Downloads"
    assert values["category"] == "Linux"
    assert values["tags"] == ["iso", "legal"]
    assert values["paused"] is True
    assert values["sequential_download"] is True
    app.processEvents()


def test_torrent_table_preserves_multi_selection_on_refresh():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from uctorrent.app.ui.torrent_table import TorrentTable

    app = QApplication.instance() or QApplication([])
    table = TorrentTable()
    first = {"id": 1, "name": "One", "status": "paused"}
    second = {"id": 2, "name": "Two", "status": "paused"}
    table.set_torrents([first, second], selected_ids=[1, 2])

    table.set_torrents([{**first, "status": "downloading"}, {**second, "status": "paused"}], selected_ids=table.selected_torrent_ids())

    assert set(table.selected_torrent_ids()) == {1, 2}
    app.processEvents()
