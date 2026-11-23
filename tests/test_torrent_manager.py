from uctorrent.app.core.torrent_manager import TorrentManager
from uctorrent.app.database.db import get_session, init_database
from uctorrent.app.database.repositories import TorrentRepository


class FakeEngine:
    def __init__(self):
        self.calls = []

    def has_handle(self, info_hash):
        return True

    def status(self, info_hash):
        return {
            "status": "downloading",
            "progress": 0.5,
            "download_rate": 1024,
            "upload_rate": 128,
            "downloaded": 100,
            "uploaded": 10,
            "seeds": 3,
            "peers": 7,
            "eta": 42,
            "availability": 1.5,
        }

    def pause(self, info_hash):
        self.calls.append(("pause", info_hash))

    def resume(self, info_hash):
        self.calls.append(("resume", info_hash))

    def remove(self, info_hash, delete_files=False):
        self.calls.append(("remove", info_hash, delete_files))

    def files(self, info_hash):
        return []

    def trackers(self, info_hash):
        return []

    def peers(self, info_hash):
        return []

    def set_file_priority(self, info_hash, file_indexes, priority):
        self.calls.append(("priority", info_hash, file_indexes, priority))


class NoStatusEngine(FakeEngine):
    def has_handle(self, info_hash):
        return False

    def status(self, info_hash):
        return {}


class RestoreEngine(NoStatusEngine):
    def restore_torrent_file(self, torrent_path, save_path, paused=True):
        self.calls.append(("restore_file", str(torrent_path), str(save_path), paused))
        return "abc123"

    def restore_magnet(self, magnet_uri, save_path, paused=True):
        self.calls.append(("restore_magnet", magnet_uri, str(save_path), paused))
        return "def456"


def setup_function():
    init_database("sqlite:///:memory:")


def test_sync_status_does_not_assign_peer_count_to_peer_relationship():
    session = get_session()
    try:
        TorrentRepository(session).create(name="Legal ISO", info_hash="abc123", status="metadata")
        session.commit()
    finally:
        session.close()

    manager = TorrentManager({})
    manager.engine = FakeEngine()

    torrents = manager.list_torrents()

    assert torrents[0]["status"] == "downloading"
    assert torrents[0]["peers"] == 7
    assert torrents[0]["seeds"] == 3
    assert torrents[0]["eta"] == 42
    assert torrents[0]["availability"] == 1.5


def test_saved_active_torrent_without_handle_becomes_offline():
    session = get_session()
    try:
        TorrentRepository(session).create(name="Legal ISO", info_hash="abc123", status="downloading")
        session.commit()
    finally:
        session.close()

    manager = TorrentManager({})
    manager.engine = NoStatusEngine()

    torrents = manager.list_torrents()

    assert torrents[0]["status"] == "offline"
    assert "sem sessao ativa" in manager.get_torrent_logs(torrents[0]["id"])[0]["message"].lower()


def test_restore_session_uses_torrent_path_and_magnet(monkeypatch, tmp_path):
    torrent_file = tmp_path / "legal.torrent"
    torrent_file.write_bytes(b"placeholder")
    session = get_session()
    try:
        repo = TorrentRepository(session)
        repo.create(name="File", info_hash="abc123", torrent_path=str(torrent_file), save_path=str(tmp_path), status="paused")
        repo.create(name="Magnet", info_hash="def456", magnet_uri="magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567", save_path=str(tmp_path), status="downloading")
        session.commit()
    finally:
        session.close()

    fake = RestoreEngine()
    import uctorrent.app.core.torrent_manager as manager_module

    monkeypatch.setattr(manager_module, "TorrentSession", lambda config: fake)
    TorrentManager({})

    assert ("restore_file", str(torrent_file), str(tmp_path), True) in fake.calls
    assert ("restore_magnet", "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567", str(tmp_path), False) in fake.calls


def test_batch_actions_call_engine_for_all_ids():
    session = get_session()
    try:
        repo = TorrentRepository(session)
        one = repo.create(name="One", info_hash="one", status="paused")
        two = repo.create(name="Two", info_hash="two", status="paused")
        session.commit()
        ids = [one.id, two.id]
    finally:
        session.close()

    manager = TorrentManager({})
    fake = FakeEngine()
    manager.engine = fake
    manager.batch_action(ids, "resume")

    assert ("resume", "one") in fake.calls
    assert ("resume", "two") in fake.calls


def test_torrent_logs_are_recorded():
    session = get_session()
    try:
        torrent = TorrentRepository(session).create(name="One", info_hash="one", status="paused")
        session.commit()
        torrent_id = torrent.id
    finally:
        session.close()

    manager = TorrentManager({})
    manager.engine = FakeEngine()
    manager.pause(torrent_id)

    logs = manager.get_torrent_logs(torrent_id)
    assert any("status alterado" in item["message"].lower() for item in logs)
