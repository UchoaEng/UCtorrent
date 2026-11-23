from __future__ import annotations

import sys

from uctorrent.app.api.server import ApiServerThread, create_app
from uctorrent.app.core.torrent_manager import TorrentManager
from uctorrent.app.database.db import init_database
from uctorrent.app.services.config_service import ConfigService
from uctorrent.app.services.log_service import LogService
from uctorrent.app.services.rss_service import RssService
from uctorrent.app.services.safety_service import SafetyService
from uctorrent.app.services.scheduler_service import SchedulerService
from uctorrent.app.services.theme_service import ThemeService
from PySide6.QtGui import QIcon

from uctorrent.app.utils.constants import APP_ICON_PATH, APP_NAME, UI_STYLE_PATH, ensure_runtime_dirs
from uctorrent.app.utils.network_utils import find_available_port


def bootstrap():
    ensure_runtime_dirs()
    init_database()
    config_service = ConfigService()
    log_service = LogService()
    safety_service = SafetyService()
    manager = TorrentManager(config_service.data, safety_service)
    if hasattr(manager.engine, "set_speed_limits"):
        manager.engine.set_speed_limits(
            int(config_service.get("speed.download_limit", 0)),
            int(config_service.get("speed.upload_limit", 0)),
        )
    scheduler = SchedulerService()
    if config_service.get("rss.enabled", True) and config_service.get("rss.auto_download", False):
        rss_service = RssService()
        interval = int(config_service.get("rss.check_interval", 300))
        scheduler.add_interval(interval, lambda: rss_service.process_automation(manager, log_service))
        scheduler.start()
    return config_service, log_service, manager, scheduler


def run_desktop() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError("PySide6 nao esta instalado. Instale as dependencias de UCtorrent.") from exc

    from uctorrent.app.ui.main_window import MainWindow

    config_service, log_service, manager, scheduler = bootstrap()
    for arg in sys.argv[1:]:
        if arg.startswith("magnet:"):
            try:
                manager.add_magnet(arg, paused=config_service.get("downloads.add_paused_by_default", False))
            except Exception as exc:
                log_service.error("app", f"Falha ao adicionar magnet recebido do sistema: {exc}")
    api_thread = None
    if config_service.get("api.enabled", True):
        app = create_app(manager, config_service)
        api_host = config_service.get("api.host", "127.0.0.1")
        configured_port = int(config_service.get("api.port", 8080))
        api_port = find_available_port(api_host, configured_port)
        if api_port != configured_port:
            log_service.warning(
                "api",
                f"Porta {configured_port} ocupada; WebUI/API de UCtorrent sera iniciada em {api_host}:{api_port}.",
            )
        api_thread = ApiServerThread(app, api_host, api_port)
        api_thread.start()
        log_service.info("api", f"WebUI/API de UCtorrent iniciada em {api_host}:{api_port}")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    app.uctorrent_base_palette = app.palette()
    theme_service = ThemeService(UI_STYLE_PATH)
    theme_name = config_service.get("app.theme", "system")
    app.setPalette(theme_service.palette(theme_name, app.uctorrent_base_palette))
    app.setStyleSheet(theme_service.load(theme_name, app.uctorrent_base_palette))
    window = MainWindow(manager, config_service, log_service)
    window.show()
    code = app.exec()
    if api_thread:
        api_thread.stop()
    scheduler.stop()
    return code


def main() -> int:
    return run_desktop()


if __name__ == "__main__":
    raise SystemExit(main())
