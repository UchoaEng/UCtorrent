from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from uctorrent.app.ui.icon_service import IconService


class SettingsWindow(QDialog):
    def __init__(self, config_service, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.setWindowTitle("UCtorrent - configuracoes")
        self.resize(720, 480)
        self.setMinimumSize(620, 420)

        self.sections = QListWidget()
        self.sections.setObjectName("settingsNav")
        self.sections.setFixedWidth(188)
        self.sections.setSpacing(3)
        self.sections.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabs = QStackedWidget()
        self._build_general_tab()
        self._build_downloads_tab()
        self._build_network_tab()
        self._build_api_tab()
        self._build_rss_tab()
        self._build_security_tab()
        self.sections.currentRowChanged.connect(self.tabs.setCurrentIndex)
        self.sections.setCurrentRow(0)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(10)
        body.addWidget(self.sections)
        body.addWidget(self.tabs, 1)
        layout.addLayout(body)
        layout.addWidget(buttons)

    def _add_section(self, page: QWidget, icon: str, label: str) -> None:
        item = QListWidgetItem(IconService.icon(icon), label)
        item.setData(Qt.UserRole, self.tabs.count())
        self.sections.addItem(item)
        self.tabs.addWidget(page)

    def _spin(self, value: int, maximum: int = 999999) -> QSpinBox:
        field = QSpinBox()
        field.setRange(0, maximum)
        field.setValue(int(value or 0))
        field.setButtonSymbols(QSpinBox.NoButtons)
        field.setMaximumWidth(240)
        return field

    def _build_general_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.theme = QComboBox()
        self.theme.addItems(["system", "light", "dark"])
        self.theme.setCurrentText(self.config_service.get("app.theme", "system"))
        self.show_notifications = QCheckBox()
        self.show_notifications.setChecked(bool(self.config_service.get("app.show_notifications", True)))
        layout.addRow("Tema", self.theme)
        layout.addRow("Notificacoes", self.show_notifications)
        self._add_section(page, "settings", "Geral")

    def _build_downloads_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.download_path = QLineEdit(self.config_service.get("downloads.completed_path", ""))
        self.incomplete_path = QLineEdit(self.config_service.get("downloads.incomplete_path", ""))
        download_path_row = self._path_row(self.download_path)
        incomplete_path_row = self._path_row(self.incomplete_path)
        self.add_paused = QCheckBox()
        self.add_paused.setChecked(bool(self.config_service.get("downloads.add_paused_by_default", False)))
        self.preallocate = QCheckBox()
        self.preallocate.setChecked(bool(self.config_service.get("downloads.preallocate", False)))
        layout.addRow("Pasta concluida", download_path_row)
        layout.addRow("Pasta incompleta", incomplete_path_row)
        layout.addRow("Adicionar pausado", self.add_paused)
        layout.addRow("Prealocar arquivos", self.preallocate)
        self._add_section(page, "download", "Downloads")

    def _path_row(self, field: QLineEdit) -> QWidget:
        button = QPushButton("Explorar")
        button.setIcon(IconService.icon("folder"))
        button.clicked.connect(lambda: self._browse_path(field))
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field)
        layout.addWidget(button)
        return row

    def _browse_path(self, field: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta", field.text())
        if path:
            field.setText(path)

    def _build_network_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.listen_port = self._spin(self.config_service.get("bittorrent.listen_port", 6881), 65535)
        self.connections_limit = self._spin(self.config_service.get("bittorrent.connections_limit", 500), 100000)
        self.download_limit = self._spin(self.config_service.get("speed.download_limit", 0))
        self.upload_limit = self._spin(self.config_service.get("speed.upload_limit", 0))
        self.dht = QCheckBox()
        self.dht.setChecked(bool(self.config_service.get("bittorrent.dht", True)))
        self.pex = QCheckBox()
        self.pex.setChecked(bool(self.config_service.get("bittorrent.pex", True)))
        self.lsd = QCheckBox()
        self.lsd.setChecked(bool(self.config_service.get("bittorrent.lsd", True)))
        self.utp = QCheckBox()
        self.utp.setChecked(bool(self.config_service.get("bittorrent.utp", True)))
        layout.addRow("Porta de escuta", self.listen_port)
        layout.addRow("Limite de conexoes", self.connections_limit)
        layout.addRow("Limite download B/s", self.download_limit)
        layout.addRow("Limite upload B/s", self.upload_limit)
        layout.addRow("DHT", self.dht)
        layout.addRow("PEX", self.pex)
        layout.addRow("LSD", self.lsd)
        layout.addRow("uTP", self.utp)
        self._add_section(page, "tracker", "Rede")

    def _build_api_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.api_enabled = QCheckBox()
        self.api_enabled.setChecked(bool(self.config_service.get("api.enabled", True)))
        self.api_host = QLineEdit(self.config_service.get("api.host", "127.0.0.1"))
        self.api_port = self._spin(self.config_service.get("api.port", 8080), 65535)
        self.api_user = QLineEdit(self.config_service.get("api.username", "admin"))
        self.api_password = QLineEdit(self.config_service.get("api.password", "admin"))
        self.api_password.setEchoMode(QLineEdit.Password)
        layout.addRow("Ativar API/WebUI", self.api_enabled)
        layout.addRow("Host", self.api_host)
        layout.addRow("Porta", self.api_port)
        layout.addRow("Usuario", self.api_user)
        layout.addRow("Senha", self.api_password)
        self._add_section(page, "activity", "API")

    def _build_rss_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.rss_enabled = QCheckBox()
        self.rss_enabled.setChecked(bool(self.config_service.get("rss.enabled", True)))
        self.rss_auto = QCheckBox()
        self.rss_auto.setChecked(bool(self.config_service.get("rss.auto_download", False)))
        self.rss_interval = self._spin(self.config_service.get("rss.check_interval", 300), 86400)
        layout.addRow("Ativar RSS", self.rss_enabled)
        layout.addRow("Auto-download por regra", self.rss_auto)
        layout.addRow("Intervalo RSS (s)", self.rss_interval)
        self._add_section(page, "rss", "RSS")

    def _build_security_tab(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        self.allow_external_paths = QCheckBox()
        self.allow_external_paths.setChecked(bool(self.config_service.get("security.allow_external_save_paths", False)))
        self.rate_limit = self._spin(self.config_service.get("security.rate_limit_per_minute", 120), 10000)
        layout.addRow("Permitir destinos externos", self.allow_external_paths)
        layout.addRow("Rate limit API/min", self.rate_limit)
        self._add_section(page, "warning", "Seguranca")

    def save(self):
        self.config_service.set("app.theme", self.theme.currentText())
        self.config_service.set("app.show_notifications", self.show_notifications.isChecked())
        self.config_service.set("downloads.completed_path", self.download_path.text())
        self.config_service.set("downloads.incomplete_path", self.incomplete_path.text())
        self.config_service.set("downloads.add_paused_by_default", self.add_paused.isChecked())
        self.config_service.set("downloads.preallocate", self.preallocate.isChecked())
        self.config_service.set("bittorrent.listen_port", self.listen_port.value())
        self.config_service.set("bittorrent.connections_limit", self.connections_limit.value())
        self.config_service.set("bittorrent.dht", self.dht.isChecked())
        self.config_service.set("bittorrent.pex", self.pex.isChecked())
        self.config_service.set("bittorrent.lsd", self.lsd.isChecked())
        self.config_service.set("bittorrent.utp", self.utp.isChecked())
        self.config_service.set("speed.download_limit", self.download_limit.value())
        self.config_service.set("speed.upload_limit", self.upload_limit.value())
        self.config_service.set("api.enabled", self.api_enabled.isChecked())
        self.config_service.set("api.host", self.api_host.text() or "127.0.0.1")
        self.config_service.set("api.port", self.api_port.value())
        self.config_service.set("api.username", self.api_user.text() or "admin")
        self.config_service.set("api.password", self.api_password.text() or "admin")
        self.config_service.set("rss.enabled", self.rss_enabled.isChecked())
        self.config_service.set("rss.auto_download", self.rss_auto.isChecked())
        self.config_service.set("rss.check_interval", self.rss_interval.value())
        self.config_service.set("security.allow_external_save_paths", self.allow_external_paths.isChecked())
        self.config_service.set("security.rate_limit_per_minute", self.rate_limit.value())
        self.accept()
