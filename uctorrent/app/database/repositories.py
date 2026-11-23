from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from uctorrent.app.database.models import (
    Category,
    LogEntry,
    RssFeed,
    RssItem,
    RssRule,
    Setting,
    Tag,
    Torrent,
    TorrentFile,
    Tracker,
)


def torrent_to_dict(torrent: Torrent) -> dict[str, Any]:
    return {
        "id": torrent.id,
        "name": torrent.name,
        "info_hash": torrent.info_hash,
        "magnet_uri": torrent.magnet_uri,
        "torrent_path": torrent.torrent_path,
        "save_path": torrent.save_path,
        "category": torrent.category.name if torrent.category else None,
        "status": torrent.status,
        "progress": torrent.progress,
        "download_rate": torrent.download_rate,
        "upload_rate": torrent.upload_rate,
        "total_size": torrent.total_size,
        "downloaded": torrent.downloaded,
        "uploaded": torrent.uploaded,
        "ratio": torrent.ratio,
        "download_limit": torrent.download_limit,
        "upload_limit": torrent.upload_limit,
        "ratio_limit": torrent.ratio_limit,
        "seed_time_limit": torrent.seed_time_limit,
        "sequential_download": torrent.sequential_download,
        "first_last_piece_priority": torrent.first_last_piece_priority,
        "super_seeding": torrent.super_seeding,
        "auto_tmm": torrent.auto_tmm,
        "priority": torrent.priority,
        "queue_position": torrent.queue_position,
        "added_at": torrent.added_at.isoformat() if torrent.added_at else None,
        "completed_at": torrent.completed_at.isoformat() if torrent.completed_at else None,
        "last_activity_at": torrent.last_activity_at.isoformat() if torrent.last_activity_at else None,
        "tags": [tag.name for tag in torrent.tags],
    }


class TorrentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Torrent]:
        return list(self.session.scalars(select(Torrent).order_by(Torrent.queue_position, Torrent.id)))

    def get(self, torrent_id: int) -> Torrent | None:
        return self.session.get(Torrent, torrent_id)

    def get_by_hash(self, info_hash: str) -> Torrent | None:
        return self.session.scalar(select(Torrent).where(Torrent.info_hash == info_hash))

    def create(self, **values: Any) -> Torrent:
        torrent = Torrent(**values)
        self.session.add(torrent)
        self.session.flush()
        return torrent

    def update(self, torrent_id: int, **values: Any) -> Torrent:
        torrent = self.get(torrent_id)
        if torrent is None:
            raise KeyError(f"Torrent {torrent_id} nao encontrado")
        for key, value in values.items():
            setattr(torrent, key, value)
        self.session.flush()
        return torrent

    def delete(self, torrent_id: int) -> None:
        torrent = self.get(torrent_id)
        if torrent is not None:
            self.session.delete(torrent)
            self.session.flush()

    def replace_files(self, torrent_id: int, files: Iterable[dict[str, Any]]) -> None:
        torrent = self.get(torrent_id)
        if torrent is None:
            raise KeyError(f"Torrent {torrent_id} nao encontrado")
        torrent.files.clear()
        for item in files:
            torrent.files.append(TorrentFile(**item))
        self.session.flush()

    def replace_trackers(self, torrent_id: int, urls: Iterable[str]) -> None:
        torrent = self.get(torrent_id)
        if torrent is None:
            raise KeyError(f"Torrent {torrent_id} nao encontrado")
        torrent.trackers.clear()
        for url in urls:
            torrent.trackers.append(Tracker(url=url))
        self.session.flush()


class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Category]:
        return list(self.session.scalars(select(Category).order_by(Category.name)))

    def get_by_name(self, name: str) -> Category | None:
        return self.session.scalar(select(Category).where(Category.name == name))

    def upsert(self, name: str, **values: Any) -> Category:
        category = self.get_by_name(name)
        if category is None:
            category = Category(name=name, **values)
            self.session.add(category)
        else:
            for key, value in values.items():
                setattr(category, key, value)
        self.session.flush()
        return category

    def delete(self, name: str) -> None:
        category = self.get_by_name(name)
        if category is not None:
            self.session.delete(category)
            self.session.flush()


class TagRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Tag]:
        return list(self.session.scalars(select(Tag).order_by(Tag.name)))

    def get_by_name(self, name: str) -> Tag | None:
        return self.session.scalar(select(Tag).where(Tag.name == name))

    def create(self, name: str) -> Tag:
        tag = self.get_by_name(name)
        if tag is None:
            tag = Tag(name=name)
            self.session.add(tag)
            self.session.flush()
        return tag

    def delete(self, name: str) -> None:
        tag = self.get_by_name(name)
        if tag is not None:
            self.session.delete(tag)
            self.session.flush()


class SettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def all(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for row in self.session.scalars(select(Setting)):
            try:
                data[row.key] = json.loads(row.value)
            except json.JSONDecodeError:
                data[row.key] = row.value
        return data

    def set(self, key: str, value: Any) -> Setting:
        setting = self.session.get(Setting, key)
        serialized = json.dumps(value, ensure_ascii=True)
        if setting is None:
            setting = Setting(key=key, value=serialized)
            self.session.add(setting)
        else:
            setting.value = serialized
        self.session.flush()
        return setting


class RssRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_feeds(self) -> list[RssFeed]:
        return list(self.session.scalars(select(RssFeed).order_by(RssFeed.name)))

    def create_feed(self, name: str, url: str, enabled: bool = True, update_interval: int = 60) -> RssFeed:
        feed = RssFeed(name=name, url=url, enabled=enabled, update_interval=update_interval)
        self.session.add(feed)
        self.session.flush()
        return feed

    def list_items(self) -> list[RssItem]:
        return list(self.session.scalars(select(RssItem).order_by(RssItem.id.desc())))

    def create_item(self, feed_id: int, title: str, url: str) -> RssItem:
        item = RssItem(feed_id=feed_id, title=title, url=url)
        self.session.add(item)
        self.session.flush()
        return item

    def list_rules(self) -> list[RssRule]:
        return list(self.session.scalars(select(RssRule).order_by(RssRule.name)))

    def create_rule(self, **values: Any) -> RssRule:
        rule = RssRule(**values)
        self.session.add(rule)
        self.session.flush()
        return rule


class LogRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, level: str, scope: str, message: str) -> LogEntry:
        entry = LogEntry(level=level.upper(), scope=scope, message=message)
        self.session.add(entry)
        self.session.flush()
        return entry

    def list(self, limit: int = 200, scope: str | None = None) -> list[LogEntry]:
        query = select(LogEntry).order_by(LogEntry.id.desc()).limit(limit)
        if scope:
            query = select(LogEntry).where(LogEntry.scope == scope).order_by(LogEntry.id.desc()).limit(limit)
        return list(self.session.scalars(query))
