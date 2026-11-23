from __future__ import annotations

from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import TagRepository


class TagService:
    def list_tags(self) -> list[dict]:
        session = get_session()
        try:
            return [{"id": tag.id, "name": tag.name} for tag in TagRepository(session).list()]
        finally:
            session.close()

    def create(self, name: str) -> dict:
        session = get_session()
        try:
            tag = TagRepository(session).create(name)
            session.commit()
            return {"id": tag.id, "name": tag.name}
        finally:
            session.close()

