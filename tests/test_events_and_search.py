from uctorrent.app.core.event_bus import EventBus
from uctorrent.app.core.torrent_manager import TorrentManager
from uctorrent.app.database.db import get_session, init_database
from uctorrent.app.database.repositories import TorrentRepository
from uctorrent.app.services.search_service import SearchService


class TrackerEngine:
    def __init__(self):
        self.calls = []

    def has_handle(self, info_hash):
        return True

    def status(self, info_hash):
        return {}

    def poll_alerts(self):
        return []

    def add_tracker(self, info_hash, url):
        self.calls.append(("add_tracker", info_hash, url))

    def remove_tracker(self, info_hash, url):
        self.calls.append(("remove_tracker", info_hash, url))

    def reannounce(self, info_hash):
        self.calls.append(("reannounce", info_hash))

    def resume(self, info_hash):
        self.calls.append(("resume", info_hash))

    def pieces(self, info_hash):
        return [0, 1, 1, 0]


def setup_function():
    init_database("sqlite:///:memory:")


def test_event_bus_tracks_events_by_id():
    bus = EventBus()
    first = bus.publish("torrent_added", {"id": 1})
    second = bus.publish("torrent_updated", {"id": 1})

    assert bus.since(0) == [first, second]
    assert bus.since(first["id"]) == [second]


def test_manager_syncs_tracker_changes_to_engine_and_events():
    session = get_session()
    try:
        torrent = TorrentRepository(session).create(name="Legal ISO", info_hash="abc123", status="paused")
        session.commit()
        torrent_id = torrent.id
    finally:
        session.close()

    bus = EventBus()
    manager = TorrentManager({}, events=bus)
    engine = TrackerEngine()
    manager.engine = engine

    manager.add_tracker(torrent_id, "udp://tracker.example:80/announce")
    manager.remove_tracker(torrent_id, "udp://tracker.example:80/announce")

    assert ("add_tracker", "abc123", "udp://tracker.example:80/announce") in engine.calls
    assert ("remove_tracker", "abc123", "udp://tracker.example:80/announce") in engine.calls
    assert [event["event"] for event in bus.since(0)] == ["tracker_updated", "tracker_updated"]


def test_manager_returns_piece_states_from_engine():
    session = get_session()
    try:
        torrent = TorrentRepository(session).create(name="Legal ISO", info_hash="abc123", status="paused")
        session.commit()
        torrent_id = torrent.id
    finally:
        session.close()

    manager = TorrentManager({}, events=EventBus())
    manager.engine = TrackerEngine()

    assert manager.get_pieces(torrent_id) == [0, 1, 1, 0]


def test_recover_sources_adds_public_trackers_and_reannounces():
    session = get_session()
    try:
        torrent = TorrentRepository(session).create(name="Legal ISO", info_hash="abc123", status="no_seeds")
        session.commit()
        torrent_id = torrent.id
    finally:
        session.close()

    manager = TorrentManager(
        {"bittorrent": {"source_recovery_trackers": ["udp://tracker.example:80/announce"]}},
        events=EventBus(),
    )
    engine = TrackerEngine()
    manager.engine = engine

    result = manager.recover_sources(torrent_id)

    assert result["status"] == "downloading"
    assert ("add_tracker", "abc123", "udp://tracker.example:80/announce") in engine.calls
    assert ("reannounce", "abc123") in engine.calls
    assert ("resume", "abc123") in engine.calls


def test_search_service_includes_public_domain_provider():
    service = SearchService()

    results = service.search("ubuntu")

    assert service.list_providers() == ["public-domain-examples"]
    assert results[0]["name"] == "Ubuntu ISO releases"
