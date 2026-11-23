# UCtorrent

UCtorrent is a Windows desktop BitTorrent client written in Python. It provides a PySide6 desktop interface, a local FastAPI WebUI/API, SQLite persistence, RSS automation, categories, tags, logs, safety checks, and a modular libtorrent-backed core.

## Legal Use

Use UCtorrent only for public files, open source releases, Linux ISOs, public datasets, public domain material, your own backups, and content distributed with permission. UCtorrent does not include piracy search plugins, illegal indexers, captcha bypass, or integrations with illegal trackers.

## Requirements

- Python 3.11+
- A libtorrent Python binding compatible with your Python and Windows build
- PySide6
- FastAPI and Uvicorn
- SQLite

Install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install libtorrent
```

Do not install `python-libtorrent` with pip for this project; on Windows that package name often has no matching distribution. Use `libtorrent`.

If `libtorrent` is not available for your Python build, install a compatible libtorrent binding from a Python version/package source that matches your platform. UCtorrent starts with a clear dependency error for real downloads until libtorrent is installed.

## Run

```powershell
python -m uctorrent.main
```

Closing the main window keeps UCtorrent running in the Windows tray. Use the tray menu to open the window again or exit the application. Theme changes in Settings are applied immediately without restarting.

## Build Windows executable

From the project root:

```powershell
.\scripts\build_exe.ps1
```

The default folder build creates:

```text
dist\UCtorrent\UCtorrent.exe
```

For a release executable that can be committed or shared as one file:

```powershell
.\scripts\build_exe.ps1 -OneFile
```

That command creates:

```text
dist\UCtorrent.exe
```

The executable stores runtime files next to itself:

```text
data\
downloads\
logs\
```

Before building, make sure the same virtual environment has a compatible `libtorrent` binding installed if real torrent transfers are needed. Build dependencies are kept in `requirements-build.txt`.

## Features

- Add `.torrent` files and magnet links.
- Drag-and-drop `.torrent` files and magnets, including batch add with shared options.
- Pause, resume, force start, remove, recheck, reannounce, recover sources, and move torrents in bulk.
- Show progress, size, status, speed, ratio, category, tags, trackers, peers, pieces, logs, and save path.
- Persist torrents, files, trackers, peers, categories, tags, RSS data, settings, and logs in SQLite.
- Restore local configuration from `data/config.json`.
- Use a local FastAPI API and lightweight WebUI.
- Manage categories and tags.
- Read RSS feeds and define rule matching helpers.
- Create `.torrent` files through libtorrent when available.
- Warn about dangerous file extensions and validate magnets, URLs, and paths.
- Support light, dark, and system themes through PySide6 QSS.
- Minimize to the Windows tray when closing the main window.

## WebUI/API

By default the local API starts on:

```text
http://127.0.0.1:8080/
```

Default development credentials:

```text
username: admin
password: admin
```

Change these in `data/config.json` before exposing the service beyond local development. CORS is restricted by configuration.

Important endpoints:

- `POST /api/auth/login`
- `GET /api/torrents`
- `POST /api/torrents/add-file`
- `POST /api/torrents/add-magnet`
- `POST /api/torrents/batch`
- `POST /api/torrents/{id}/pause`
- `POST /api/torrents/{id}/resume`
- `POST /api/torrents/{id}/remove`
- `GET /api/categories`
- `GET /api/tags`
- `GET /api/rss/feeds`
- `GET /api/logs`
- `WebSocket /api/events`

## Project Structure

```text
uctorrent/
  main.py
  app/
    core/
    ui/
    api/
    database/
    services/
    utils/
  web/
data/
downloads/
logs/
tests/
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q uctorrent tests
```

The tests cover validation, formatting, config read/write, SQLite CRUD, RSS rules, safety checks, API auth, API torrent listing, batch behavior, desktop UI logic, theme switching, and executable-safe API logging.

## Git/release hygiene

- Do not commit `.venv/`, `build/`, `UCtorrent.spec`, logs, local database, local config, session state, or downloaded files.
- The folder build under `dist\UCtorrent\` is ignored.
- The single-file release executable `dist\UCtorrent.exe` is intentionally allowed by `.gitignore`.
- Run `.\scripts\build_exe.ps1 -OneFile` after code or documentation changes when preparing a release commit that includes the executable.

## Known Limitations

- Real BitTorrent transfer requires a compatible libtorrent Python binding.
- The initial WebUI is intentionally lightweight; the desktop UI is the primary interface.
- Some advanced libtorrent features are exposed through clean abstractions and can be expanded as binding support is verified on the target machine.

## Troubleshooting

- If the desktop does not open, confirm `PySide6` is installed in the active virtual environment.
- If adding torrents reports that libtorrent is unavailable, try `python -m pip install libtorrent` inside the active virtual environment.
- If port `8080` is unavailable, UCtorrent automatically tries the next free port and writes the selected WebUI/API URL to the log.
- Logs are written to `logs/app.log` and the SQLite `logs` table.
