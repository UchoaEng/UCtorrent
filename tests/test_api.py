from fastapi.testclient import TestClient

from uctorrent.app.api.server import ApiServerThread, create_app
from uctorrent.app.database.db import init_database
from uctorrent.app.services.config_service import ConfigService


def setup_function():
    init_database("sqlite:///:memory:")


def test_api_auth_and_torrent_list(tmp_path):
    config_path = tmp_path / "config.json"
    config = ConfigService(config_path)
    app = create_app(config_service=config)
    client = TestClient(app)

    unauthorized = client.get("/api/torrents")
    assert unauthorized.status_code == 401

    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["token"]

    torrents = client.get("/api/torrents", headers={"Authorization": f"Bearer {token}"})
    assert torrents.status_code == 200
    assert torrents.json() == []


def test_api_server_config_does_not_require_stdout(monkeypatch):
    monkeypatch.setattr("sys.stdout", None)
    app = create_app(config_service=ConfigService())
    config = ApiServerThread(app, "127.0.0.1", 0)._create_config()

    assert config.log_config is None
    assert config.access_log is False
