from __future__ import annotations

import sys
from pathlib import Path


class MagnetHandlerService:
    def is_supported(self) -> bool:
        return sys.platform.startswith("win")

    def register_windows(self, command: str) -> None:
        if not self.is_supported():
            raise RuntimeError("Registro magnet:// automatico esta disponivel apenas no Windows nesta versao.")
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\magnet") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:Magnet Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\magnet\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    def unregister_windows(self) -> None:
        if not self.is_supported():
            raise RuntimeError("Registro magnet:// automatico esta disponivel apenas no Windows nesta versao.")
        import winreg

        path = r"Software\Classes\magnet\shell\open\command"
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\magnet\shell\open")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\magnet\shell")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\magnet")
        except FileNotFoundError:
            return

    def default_command(self) -> str:
        exe = Path(sys.executable)
        return f'"{exe}" -m uctorrent.main "%1"'


magnet_handler_service = MagnetHandlerService()
