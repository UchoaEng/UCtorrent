from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uctorrent.app.database.db import Base


def now() -> datetime:
    return datetime.now(UTC)


class Torrent(Base):
    __tablename__ = "torrents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    info_hash: Mapped[str | None] = mapped_column(String(80), unique=True)
    magnet_uri: Mapped[str | None] = mapped_column(Text)
    torrent_path: Mapped[str | None] = mapped_column(Text)
    save_path: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    status: Mapped[str] = mapped_column(String(64), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    download_rate: Mapped[int] = mapped_column(Integer, default=0)
    upload_rate: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(Integer, default=0)
    downloaded: Mapped[int] = mapped_column(Integer, default=0)
    uploaded: Mapped[int] = mapped_column(Integer, default=0)
    ratio: Mapped[float] = mapped_column(Float, default=0.0)
    download_limit: Mapped[int] = mapped_column(Integer, default=0)
    upload_limit: Mapped[int] = mapped_column(Integer, default=0)
    ratio_limit: Mapped[float | None] = mapped_column(Float)
    seed_time_limit: Mapped[int | None] = mapped_column(Integer)
    sequential_download: Mapped[bool] = mapped_column(Boolean, default=False)
    first_last_piece_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    super_seeding: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_tmm: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    queue_position: Mapped[int] = mapped_column(Integer, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    category: Mapped["Category | None"] = relationship(back_populates="torrents")
    files: Mapped[list["TorrentFile"]] = relationship(cascade="all, delete-orphan", back_populates="torrent")
    trackers: Mapped[list["Tracker"]] = relationship(cascade="all, delete-orphan", back_populates="torrent")
    peers: Mapped[list["Peer"]] = relationship(cascade="all, delete-orphan", back_populates="torrent")
    tags: Mapped[list["Tag"]] = relationship(secondary="torrent_tags", back_populates="torrents")


class TorrentFile(Base):
    __tablename__ = "torrent_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id"), nullable=False)
    file_index: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    wanted: Mapped[bool] = mapped_column(Boolean, default=True)

    torrent: Mapped[Torrent] = relationship(back_populates="files")


class Tracker(Base):
    __tablename__ = "trackers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str | None] = mapped_column(String(128))
    message: Mapped[str | None] = mapped_column(Text)
    seeds: Mapped[int] = mapped_column(Integer, default=0)
    peers: Mapped[int] = mapped_column(Integer, default=0)

    torrent: Mapped[Torrent] = relationship(back_populates="trackers")


class Peer(Base):
    __tablename__ = "peers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id"), nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=0)
    client: Mapped[str | None] = mapped_column(String(255))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    download_rate: Mapped[int] = mapped_column(Integer, default=0)
    upload_rate: Mapped[int] = mapped_column(Integer, default=0)
    flags: Mapped[str | None] = mapped_column(String(255))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    torrent: Mapped[Torrent] = relationship(back_populates="peers")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    save_path: Mapped[str | None] = mapped_column(Text)
    download_limit: Mapped[int | None] = mapped_column(Integer)
    upload_limit: Mapped[int | None] = mapped_column(Integer)
    ratio_limit: Mapped[float | None] = mapped_column(Float)
    seed_time_limit: Mapped[int | None] = mapped_column(Integer)

    torrents: Mapped[list[Torrent]] = relationship(back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    torrents: Mapped[list[Torrent]] = relationship(secondary="torrent_tags", back_populates="tags")


class TorrentTag(Base):
    __tablename__ = "torrent_tags"
    __table_args__ = (UniqueConstraint("torrent_id", "tag_id"),)

    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class RssFeed(Base):
    __tablename__ = "rss_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    update_interval: Mapped[int] = mapped_column(Integer, default=60)
    last_update_at: Mapped[datetime | None] = mapped_column(DateTime)

    items: Mapped[list["RssItem"]] = relationship(cascade="all, delete-orphan", back_populates="feed")
    rules: Mapped[list["RssRule"]] = relationship(cascade="all, delete-orphan", back_populates="feed")


class RssItem(Base):
    __tablename__ = "rss_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("rss_feeds.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)

    feed: Mapped[RssFeed] = relationship(back_populates="items")


class RssRule(Base):
    __tablename__ = "rss_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    feed_id: Mapped[int | None] = mapped_column(ForeignKey("rss_feeds.id"))
    must_contain: Mapped[str | None] = mapped_column(Text)
    must_not_contain: Mapped[str | None] = mapped_column(Text)
    regex: Mapped[str | None] = mapped_column(Text)
    save_path: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    tags: Mapped[str | None] = mapped_column(Text)
    add_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    feed: Mapped[RssFeed | None] = relationship(back_populates="rules")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class LogEntry(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
