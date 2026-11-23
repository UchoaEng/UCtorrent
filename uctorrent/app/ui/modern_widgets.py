from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from uctorrent.app.ui.icon_service import IconService
from uctorrent.app.utils.constants import APP_ICON_PATH, APP_NAME
from uctorrent.app.utils.formatters import format_speed


class MetricPill(QFrame):
    def __init__(self, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricPill")
        self.setFixedHeight(42)
        self.setMinimumWidth(92)
        self.setMaximumWidth(150)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 5, 9, 5)
        layout.setSpacing(7)
        icon = QLabel()
        icon.setObjectName("metricIcon")
        icon.setPixmap(IconService.icon(icon_name).pixmap(16, 16))
        layout.addWidget(icon)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(0)
        self.value = QLabel("0 B/s")
        self.value.setObjectName("metricValue")
        caption = QLabel(label)
        caption.setObjectName("metricLabel")
        text.addWidget(self.value)
        text.addWidget(caption)
        layout.addLayout(text)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class CommandHeader(QWidget):
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appHeader")
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.logo = QLabel()
        self.logo.setObjectName("headerLogo")
        self.logo.setPixmap(QIcon(str(APP_ICON_PATH)).pixmap(28, 28))
        layout.addWidget(self.logo)

        self.title_box = QWidget()
        title_box = QVBoxLayout(self.title_box)
        title_box.setContentsMargins(0, 0, 8, 0)
        title_box.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setObjectName("brandTitle")
        subtitle = QLabel("Desktop torrent manager")
        subtitle.setObjectName("brandSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addWidget(self.title_box)

        self.download = MetricPill("download", "download")
        self.upload = MetricPill("upload", "upload")
        self.active = MetricPill("activity", "ativos")
        layout.addWidget(self.download)
        layout.addWidget(self.upload)
        layout.addWidget(self.active)
        layout.addStretch(1)

        self.search = QLineEdit()
        self.search.setObjectName("headerSearch")
        self.search.setPlaceholderText("Pesquisar torrents")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(140)
        self.search.setMaximumWidth(300)
        self.search.setFixedHeight(34)
        self.search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search)

    def update_metrics(self, download_rate: int | float, upload_rate: int | float, active: int) -> None:
        self.download.set_value(format_speed(download_rate))
        self.upload.set_value(format_speed(upload_rate))
        self.active.set_value(str(active))

    def resizeEvent(self, event) -> None:
        width = event.size().width()
        self.title_box.setVisible(width >= 720)
        self.upload.setVisible(width >= 560)
        self.search.setVisible(width >= 640)
        super().resizeEvent(event)


class ToastManager(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.hide()
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self._animation_finished)
        self._hiding = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)

    def show_message(self, text: str, timeout: int = 2400) -> None:
        self.setText(text)
        self.adjustSize()
        self.move((self.parentWidget().width() - self.width()) // 2, 18)
        self.effect.setOpacity(0)
        self._hiding = False
        self.show()
        self.raise_()
        self.animation.stop()
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
        self.timer.start(timeout)

    def hide_toast(self) -> None:
        self._hiding = True
        self.animation.stop()
        self.animation.setStartValue(self.effect.opacity())
        self.animation.setEndValue(0)
        self.animation.start()

    def _animation_finished(self) -> None:
        if self._hiding:
            self.hide()


class DropOverlay(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("dropOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        icon = QLabel()
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(IconService.icon("torrent").pixmap(42, 42))
        label = QLabel("Solte torrents ou magnets para adicionar")
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("dropOverlayLabel")
        layout.addWidget(icon)
        layout.addWidget(label)

    def resize_to_parent(self) -> None:
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
