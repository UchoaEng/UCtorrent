from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "UCtorrent"
LEGAL_NOTICE = (
    "UCtorrent deve ser usado apenas com arquivos publicos, open source, "
    "ISOs Linux, datasets, dominio publico, backups proprios e conteudos "
    "distribuidos com autorizacao."
)

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
    PACKAGE_DIR = Path(getattr(sys, "_MEIPASS", ROOT_DIR)) / "uctorrent"
else:
    ROOT_DIR = Path(__file__).resolve().parents[3]
    PACKAGE_DIR = ROOT_DIR / "uctorrent"
ASSETS_DIR = PACKAGE_DIR / "app" / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
DATA_DIR = ROOT_DIR / "data"
DOWNLOADS_DIR = ROOT_DIR / "downloads"
INCOMPLETE_DIR = DOWNLOADS_DIR / "incomplete"
COMPLETED_DIR = DOWNLOADS_DIR / "completed"
LOGS_DIR = ROOT_DIR / "logs"
WEB_DIR = PACKAGE_DIR / "web"
UI_STYLE_PATH = PACKAGE_DIR / "app" / "ui" / "styles.qss"
APP_ICON_PATH = ASSETS_DIR / "uctorrent-logo.png"

CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "app.db"
LOG_PATH = LOGS_DIR / "app.log"
SESSION_STATE_PATH = DATA_DIR / "session_state.bin"

DANGEROUS_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".msi",
    ".scr",
    ".ps1",
    ".vbs",
    ".jar",
    ".apk",
    ".com",
}

TORRENT_STATUSES = {
    "downloading": "Baixando",
    "paused": "Pausado",
    "finished": "Finalizado",
    "seeding": "Semeando",
    "checking": "Verificando",
    "metadata": "Obtendo metadados",
    "queued": "Na fila",
    "error": "Erro",
    "offline": "Sem conexao",
    "no_seeds": "Sem seeds",
    "moving": "Movendo arquivos",
    "allocating": "Alocando espaco",
}


def ensure_runtime_dirs() -> None:
    for path in (DATA_DIR, INCOMPLETE_DIR, COMPLETED_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)
