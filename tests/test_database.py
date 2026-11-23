from uctorrent.app.database.db import get_session, init_database
from uctorrent.app.database.repositories import CategoryRepository, RssRepository, TagRepository, TorrentRepository


def setup_function():
    init_database("sqlite:///:memory:")


def test_torrent_crud():
    session = get_session()
    try:
        repo = TorrentRepository(session)
        torrent = repo.create(name="Ubuntu ISO", info_hash="abc", status="paused")
        session.commit()
        assert repo.get(torrent.id).name == "Ubuntu ISO"
        repo.update(torrent.id, status="downloading")
        session.commit()
        assert repo.get(torrent.id).status == "downloading"
        repo.delete(torrent.id)
        session.commit()
        assert repo.get(torrent.id) is None
    finally:
        session.close()


def test_category_and_tag_crud():
    session = get_session()
    try:
        cat = CategoryRepository(session).upsert("Linux", save_path="downloads/completed")
        tag = TagRepository(session).create("iso")
        session.commit()
        assert cat.name == "Linux"
        assert tag.name == "iso"
        assert len(CategoryRepository(session).list()) == 1
        assert len(TagRepository(session).list()) == 1
    finally:
        session.close()


def test_rss_crud():
    session = get_session()
    try:
        repo = RssRepository(session)
        feed = repo.create_feed("Legal Feed", "https://example.com/feed.xml")
        item = repo.create_item(feed.id, "Public dataset", "https://example.com/dataset.torrent")
        rule = repo.create_rule(name="dataset", must_contain="dataset")
        session.commit()
        assert repo.list_feeds()[0].name == "Legal Feed"
        assert item.title == "Public dataset"
        assert rule.name == "dataset"
    finally:
        session.close()

