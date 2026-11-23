from __future__ import annotations

from datetime import datetime
from typing import Any

from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import RssRepository
from uctorrent.app.services.rss_rules_service import RssRulesService
from uctorrent.app.utils.validators import is_valid_http_url


class RssService:
    def list_feeds(self) -> list[dict]:
        session = get_session()
        try:
            return [
                {
                    "id": feed.id,
                    "name": feed.name,
                    "url": feed.url,
                    "enabled": feed.enabled,
                    "update_interval": feed.update_interval,
                    "last_update_at": feed.last_update_at.isoformat() if feed.last_update_at else None,
                }
                for feed in RssRepository(session).list_feeds()
            ]
        finally:
            session.close()

    def add_feed(self, name: str, url: str, update_interval: int = 60) -> dict:
        if not is_valid_http_url(url):
            raise ValueError("Feed RSS deve usar URL http ou https.")
        session = get_session()
        try:
            feed = RssRepository(session).create_feed(name, url, True, update_interval)
            session.commit()
            return {"id": feed.id, "name": feed.name, "url": feed.url}
        finally:
            session.close()

    def refresh_feed(self, feed_id: int) -> list[dict]:
        try:
            import feedparser
        except ImportError as exc:
            raise RuntimeError("feedparser nao esta instalado.") from exc

        session = get_session()
        try:
            repo = RssRepository(session)
            feed = next((item for item in repo.list_feeds() if item.id == feed_id), None)
            if feed is None:
                raise KeyError("Feed nao encontrado.")
            parsed = feedparser.parse(feed.url)
            items = []
            existing_urls = {item.url for item in repo.list_items()}
            for entry in parsed.entries:
                link = getattr(entry, "link", "")
                for enclosure in getattr(entry, "enclosures", []) or []:
                    href = getattr(enclosure, "href", "") or enclosure.get("href", "")
                    if href.startswith("magnet:"):
                        link = href
                        break
                title = getattr(entry, "title", link)
                if link and link not in existing_urls:
                    item = repo.create_item(feed.id, title, link)
                    items.append({"id": item.id, "title": item.title, "url": item.url})
            feed.last_update_at = datetime.utcnow()
            session.commit()
            return items
        finally:
            session.close()

    def list_rules(self) -> list[dict[str, Any]]:
        session = get_session()
        try:
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "enabled": item.enabled,
                    "feed_id": item.feed_id,
                    "must_contain": item.must_contain,
                    "must_not_contain": item.must_not_contain,
                    "regex": item.regex,
                    "save_path": item.save_path,
                    "category_id": item.category_id,
                    "tags": item.tags,
                    "add_paused": item.add_paused,
                }
                for item in RssRepository(session).list_rules()
            ]
        finally:
            session.close()

    def process_automation(self, manager, log_service=None) -> list[dict[str, Any]]:
        rules = [rule for rule in self.list_rules() if rule.get("enabled")]
        if not rules:
            return []
        added = []
        matcher = RssRulesService()
        session = get_session()
        try:
            repo = RssRepository(session)
            feeds = [feed for feed in repo.list_feeds() if feed.enabled]
        finally:
            session.close()
        for feed in feeds:
            try:
                new_items = self.refresh_feed(feed.id)
            except Exception as exc:
                if log_service:
                    log_service.warning("rss", f"Falha ao atualizar feed {feed.name}: {exc}")
                continue
            for item in new_items:
                for rule in rules:
                    if rule.get("feed_id") not in (None, feed.id):
                        continue
                    if not matcher.matches_item(item, rule):
                        continue
                    if not item["url"].startswith("magnet:"):
                        continue
                    tags = [tag.strip() for tag in (rule.get("tags") or "").split(",") if tag.strip()]
                    torrent = manager.add_magnet(
                        item["url"],
                        save_path=rule.get("save_path") or None,
                        paused=bool(rule.get("add_paused")),
                        tags=tags,
                        name=item["title"],
                    )
                    self._mark_downloaded(item["id"])
                    added.append({"rss_item": item, "torrent": torrent, "rule": rule})
                    if log_service:
                        log_service.info("rss", f"RSS auto-adicionou: {item['title']}")
                    break
        return added

    def _mark_downloaded(self, item_id: int) -> None:
        session = get_session()
        try:
            item = next((row for row in RssRepository(session).list_items() if row.id == item_id), None)
            if item:
                item.downloaded = True
                session.commit()
        finally:
            session.close()
