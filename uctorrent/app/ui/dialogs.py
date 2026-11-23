from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from uctorrent.app.utils.constants import LEGAL_NOTICE


def show_error(parent: QWidget | None, title: str, message: str) -> None:
    QMessageBox.critical(parent, title, message)


def confirm(parent: QWidget | None, title: str, message: str) -> bool:
    return QMessageBox.question(parent, title, message) == QMessageBox.Yes


def show_legal_notice(parent: QWidget | None) -> bool:
    box = QMessageBox(parent)
    box.setWindowTitle("UCtorrent - aviso de uso legal")
    box.setText(LEGAL_NOTICE)
    box.setInformativeText("Voce confirma que usara UCtorrent apenas com conteudo legal ou autorizado?")
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return box.exec() == QMessageBox.Yes

