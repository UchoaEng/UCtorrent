from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from uctorrent.app.utils.constants import APP_ICON_PATH


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(QIcon(str(APP_ICON_PATH)), parent)
        self.setToolTip("UCtorrent")
        if parent is not None:
            menu = QMenu(parent)
            menu.addAction("Abrir UCtorrent", parent.show_from_tray)
            menu.addAction("Ocultar", parent.hide)
            menu.addSeparator()
            menu.addAction("Sair", parent.quit_application)
            self.setContextMenu(menu)
            self.activated.connect(self._handle_activation)

    def _handle_activation(self, reason) -> None:
        if reason in {QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick} and self.parent():
            self.parent().show_from_tray()
