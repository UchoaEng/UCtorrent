from pathlib import Path

import pytest

from uctorrent.app.services.config_service import ConfigService
from uctorrent.app.services.safety_service import SafetyService
from uctorrent.app.utils.formatters import format_bytes, format_speed
from uctorrent.app.utils.magnet_utils import extract_magnets, extract_magnets_from_file
from uctorrent.app.utils.validators import is_valid_magnet


VALID_MAGNET = "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567&dn=legal"


def test_magnet_validation():
    assert is_valid_magnet(VALID_MAGNET)
    assert not is_valid_magnet("https://example.com/file.torrent")


def test_extract_magnets_from_text_and_file(tmp_path: Path):
    other = "magnet:?xt=urn:btih:abcdefabcdefabcdefabcdefabcdefabcdefabcd&dn=other"
    text = f"Baixar {VALID_MAGNET}\nDuplicado {VALID_MAGNET}\nOutro: {other}"
    magnet_file = tmp_path / "legal.magnet"
    magnet_file.write_text(text, encoding="utf-8")
    ignored = tmp_path / "legal.bin"
    ignored.write_text(text, encoding="utf-8")

    assert extract_magnets(text) == [VALID_MAGNET, other]
    assert extract_magnets_from_file(magnet_file) == [VALID_MAGNET, other]
    assert extract_magnets_from_file(ignored) == []


def test_formatters():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_speed(1024) == "1.00 KB/s"


def test_config_read_write(tmp_path: Path):
    path = tmp_path / "config.json"
    service = ConfigService(path)
    service.set("api.port", 9090)
    reloaded = ConfigService(path)
    assert reloaded.get("api.port") == 9090


def test_safety_service():
    safety = SafetyService()
    safety.validate_magnet(VALID_MAGNET)
    with pytest.raises(ValueError):
        safety.validate_url("ftp://example.com/file.torrent")
    assert safety.dangerous_files(["safe.txt", "setup.exe"]) == ["setup.exe"]
    with pytest.raises(ValueError):
        safety.validate_relative_path("../escape")
