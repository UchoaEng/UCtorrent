from __future__ import annotations

from fastapi import APIRouter, Depends

from uctorrent.app.api.auth import require_auth
from uctorrent.app.api.schemas import RssFeedIn, RssRuleIn
from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import RssRepository
from uctorrent.app.services.rss_service import RssService


router = APIRouter(prefix="/api/rss", tags=["rss"], dependencies=[Depends(require_auth)])
rss_service = RssService()


@router.get("/feeds")
def feeds():
    return rss_service.list_feeds()


@router.post("/feeds")
def add_feed(payload: RssFeedIn):
    feed = rss_service.add_feed(payload.name, payload.url, payload.update_interval)
    if not payload.enabled:
        update_feed(feed["id"], payload)
    return feed


@router.post("/feeds/{feed_id}/refresh")
def refresh_feed(feed_id: int):
    return rss_service.refresh_feed(feed_id)


@router.put("/feeds/{feed_id}")
def update_feed(feed_id: int, payload: RssFeedIn):
    session = get_session()
    try:
        feed = next((item for item in RssRepository(session).list_feeds() if item.id == feed_id), None)
        if feed is None:
            return {"ok": False}
        for key, value in payload.model_dump().items():
            setattr(feed, key, value)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.delete("/feeds/{feed_id}")
def delete_feed(feed_id: int):
    session = get_session()
    try:
        feed = next((item for item in RssRepository(session).list_feeds() if item.id == feed_id), None)
        if feed:
            session.delete(feed)
            session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.get("/items")
def items():
    session = get_session()
    try:
        return [{"id": item.id, "feed_id": item.feed_id, "title": item.title, "url": item.url, "read": item.read, "downloaded": item.downloaded} for item in RssRepository(session).list_items()]
    finally:
        session.close()


@router.post("/rules")
def create_rule(payload: RssRuleIn):
    session = get_session()
    try:
        rule = RssRepository(session).create_rule(**payload.model_dump())
        session.commit()
        return {"id": rule.id, "name": rule.name}
    finally:
        session.close()


@router.get("/rules")
def rules():
    return rss_service.list_rules()


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, payload: RssRuleIn):
    session = get_session()
    try:
        rule = next((item for item in RssRepository(session).list_rules() if item.id == rule_id), None)
        if rule is None:
            return {"ok": False}
        for key, value in payload.model_dump().items():
            setattr(rule, key, value)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    session = get_session()
    try:
        rule = next((item for item in RssRepository(session).list_rules() if item.id == rule_id), None)
        if rule:
            session.delete(rule)
            session.commit()
        return {"ok": True}
    finally:
        session.close()
