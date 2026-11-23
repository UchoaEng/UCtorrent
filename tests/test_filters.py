from uctorrent.app.core.torrent_filters import STATUS_FILTERS, filter_torrents


def test_filters_by_status_category_tag_and_text():
    torrents = [
        {"name": "Ubuntu ISO", "status": "downloading", "category": "Linux", "tags": ["iso"]},
        {"name": "Dataset", "status": "paused", "category": "Dados", "tags": ["publico"]},
    ]

    assert len(filter_torrents(torrents, status=STATUS_FILTERS["Baixando"])) == 1
    assert filter_torrents(torrents, category="Dados")[0]["name"] == "Dataset"
    assert filter_torrents(torrents, tag="iso")[0]["name"] == "Ubuntu ISO"
    assert filter_torrents(torrents, text="publico")[0]["name"] == "Dataset"
