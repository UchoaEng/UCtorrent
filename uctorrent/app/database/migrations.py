from __future__ import annotations

from sqlalchemy import inspect, text

from uctorrent.app.database.db import init_database


def run_migrations(db_url: str | None = None) -> None:
    engine = init_database(db_url)
    migrate_existing_database(engine)


def migrate_existing_database(engine) -> None:
    inspector = inspect(engine)
    if "torrents" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("torrents")}
    columns = {
        "download_limit": "INTEGER DEFAULT 0",
        "upload_limit": "INTEGER DEFAULT 0",
        "ratio_limit": "FLOAT",
        "seed_time_limit": "INTEGER",
        "sequential_download": "BOOLEAN DEFAULT 0",
        "first_last_piece_priority": "BOOLEAN DEFAULT 0",
        "super_seeding": "BOOLEAN DEFAULT 0",
        "auto_tmm": "BOOLEAN DEFAULT 0",
    }
    with engine.begin() as connection:
        for name, ddl in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE torrents ADD COLUMN {name} {ddl}"))
