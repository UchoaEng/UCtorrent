from __future__ import annotations

from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import CategoryRepository


class CategoryService:
    def list_categories(self) -> list[dict]:
        session = get_session()
        try:
            return [{"id": row.id, "name": row.name, "save_path": row.save_path} for row in CategoryRepository(session).list()]
        finally:
            session.close()

    def upsert(self, name: str, **values):
        session = get_session()
        try:
            category = CategoryRepository(session).upsert(name, **values)
            session.commit()
            return {"id": category.id, "name": category.name, "save_path": category.save_path}
        finally:
            session.close()
