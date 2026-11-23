from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from uctorrent.app.utils.constants import DB_PATH, ensure_runtime_dirs


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def init_database(db_url: str | None = None):
    global _engine, _SessionLocal
    ensure_runtime_dirs()
    url = db_url or f"sqlite:///{Path(DB_PATH).as_posix()}"
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    kwargs = {}
    if url == "sqlite:///:memory:":
        kwargs["poolclass"] = StaticPool
    _engine = create_engine(url, connect_args=connect_args, future=True, **kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)
    from uctorrent.app.database import models  # noqa: F401

    Base.metadata.create_all(_engine)
    from uctorrent.app.database.migrations import migrate_existing_database

    migrate_existing_database(_engine)
    return _engine


def get_engine():
    if _engine is None:
        return init_database()
    return _engine


def get_session() -> Session:
    if _SessionLocal is None:
        init_database()
    assert _SessionLocal is not None
    return _SessionLocal()


def session_scope() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
