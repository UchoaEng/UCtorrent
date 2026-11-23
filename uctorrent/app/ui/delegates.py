from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from uctorrent.app.utils.constants import TORRENT_STATUSES


PROGRESS_ROLE = Qt.UserRole + 20
STATUS_ROLE = Qt.UserRole + 21


STATUS_COLORS = {
    "downloading": ("#2563eb", "#dbeafe"),
    "seeding": ("#16a34a", "#dcfce7"),
    "finished": ("#15803d", "#dcfce7"),
    "paused": ("#64748b", "#e2e8f0"),
    "checking": ("#7c3aed", "#ede9fe"),
    "metadata": ("#0891b2", "#cffafe"),
    "queued": ("#0f766e", "#ccfbf1"),
    "error": ("#dc2626", "#fee2e2"),
    "offline": ("#475569", "#e2e8f0"),
    "no_seeds": ("#d97706", "#fef3c7"),
    "moving": ("#2563eb", "#dbeafe"),
    "allocating": ("#7c3aed", "#ede9fe"),
}


class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        progress = float(index.data(PROGRESS_ROLE) or 0)
        percent = max(0, min(int(progress * 100), 100))
        rect = option.rect.adjusted(8, 10, -8, -10)
        radius = rect.height() / 2
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        track = QColor("#bfdbfe") if option.state & QStyle.State_Selected else QColor("#e2e8f0")
        fill = QColor("#2563eb")
        painter.setPen(Qt.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(rect), radius, radius)
        fill_rect = QRectF(rect)
        fill_rect.setWidth(max(4, rect.width() * percent / 100))
        painter.setBrush(fill)
        painter.drawRoundedRect(fill_rect, radius, radius)
        painter.setPen(QColor("#0f172a"))
        font = QFont(option.font)
        font.setPointSize(max(7, font.pointSize() - 1))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(option.rect, Qt.AlignCenter, f"{percent}%")
        painter.restore()


class StatusBadgeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        status = str(index.data(STATUS_ROLE) or "")
        label = TORRENT_STATUSES.get(status, status)
        foreground, background = STATUS_COLORS.get(status, ("#2563eb", "#dbeafe"))
        rect = option.rect.adjusted(7, 7, -7, -7)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(foreground), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(QRectF(rect), 9, 9)
        font = QFont(option.font)
        font.setPointSize(max(7, font.pointSize() - 1))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(foreground))
        painter.drawText(rect.adjusted(9, 0, -9, 0), Qt.AlignVCenter | Qt.AlignLeft, label)
        painter.restore()
