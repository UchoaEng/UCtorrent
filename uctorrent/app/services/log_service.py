from __future__ import annotations

import logging

from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import LogRepository
from uctorrent.app.utils.constants import APP_NAME, LOG_PATH, ensure_runtime_dirs


def setup_logging() -> logging.Logger:
    ensure_runtime_dirs()
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(scope)s %(message)s")
        file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger


class LogService:
    def __init__(self):
        self.logger = setup_logging()

    def log(self, level: str, scope: str, message: str) -> None:
        extra = {"scope": scope}
        getattr(self.logger, level.lower(), self.logger.info)(message, extra=extra)
        try:
            session = get_session()
            LogRepository(session).add(level, scope, message)
            session.commit()
        except Exception:
            self.logger.exception("Falha ao registrar log no banco", extra=extra)
        finally:
            try:
                session.close()
            except Exception:
                pass

    def info(self, scope: str, message: str) -> None:
        self.log("INFO", scope, message)

    def warning(self, scope: str, message: str) -> None:
        self.log("WARNING", scope, message)

    def error(self, scope: str, message: str) -> None:
        self.log("ERROR", scope, message)

