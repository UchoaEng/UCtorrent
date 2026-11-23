from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import warnings

from uctorrent.app.utils.formatters import display_text

try:
    import libtorrent as lt  # type: ignore
except ImportError:  # pragma: no cover - depends on host install
    try:
        import python_libtorrent as lt  # type: ignore
    except ImportError:
        lt = None  # type: ignore


class TorrentEngineUnavailable(RuntimeError):
    pass


@dataclass
class TorrentAddResult:
    info_hash: str
    name: str
    total_size: int
    files: list[dict[str, Any]]
    trackers: list[str]


class TorrentSession:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.session = None
        self.handles: dict[str, Any] = {}
        if lt is not None:
            self._create_session()

    @property
    def available(self) -> bool:
        return lt is not None and self.session is not None

    def require_available(self) -> None:
        if not self.available:
            raise TorrentEngineUnavailable(
                "libtorrent nao esta instalado. Instale os bindings para habilitar downloads reais."
            )

    def _create_session(self) -> None:
        settings = {
            "enable_dht": bool(self.config.get("dht", True)),
            "enable_lsd": bool(self.config.get("lsd", True)),
            "enable_upnp": True,
            "enable_natpmp": True,
            "announce_to_all_trackers": True,
            "announce_to_all_tiers": True,
        }
        self.session = lt.session(settings) if hasattr(lt, "session") else None
        if self.session is None:
            return
        self.apply_settings()
        port = int(self.config.get("listen_port", 6881))
        try:
            self.session.apply_settings({"listen_interfaces": f"0.0.0.0:{port}"})
        except Exception:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    self.session.listen_on(port, port + 10)
            except Exception:
                pass

    def apply_settings(self) -> None:
        if self.session is None or lt is None:
            return
        settings = {
            "enable_dht": bool(self.config.get("dht", True)),
            "enable_pex": bool(self.config.get("pex", True)),
            "enable_lsd": bool(self.config.get("lsd", True)),
            "enable_outgoing_utp": bool(self.config.get("utp", True)),
            "enable_incoming_utp": bool(self.config.get("utp", True)),
            "connections_limit": int(self.config.get("connections_limit", 500)),
            "connections_slack": int(self.config.get("connections_slack", 10)),
        }
        try:
            self.session.apply_settings(settings)
            return
        except Exception:
            pass
        pack = getattr(lt, "settings_pack", None)
        if pack is None:
            return
        try:
            sp = pack()
            bools = {
                "enable_dht": settings["enable_dht"],
                "enable_pex": settings["enable_pex"],
                "enable_lsd": settings["enable_lsd"],
                "enable_outgoing_utp": settings["enable_outgoing_utp"],
                "enable_incoming_utp": settings["enable_incoming_utp"],
            }
            ints = {
                "connections_limit": settings["connections_limit"],
                "connections_slack": settings["connections_slack"],
            }
            for name, value in bools.items():
                key = getattr(pack, name, None)
                if key is not None:
                    sp.set_bool_value(key, bool(value))
            for name, value in ints.items():
                key = getattr(pack, name, None)
                if key is not None:
                    sp.set_int_value(key, int(value))
            self.session.apply_settings(sp)
        except Exception:
            pass
        try:
            self.session.start_dht()
            self.session.start_lsd()
        except Exception:
            pass

    def add_torrent_file(
        self,
        torrent_path: Path,
        save_path: Path,
        paused: bool = False,
        sequential_download: bool = False,
        first_last_piece_priority: bool = False,
    ) -> TorrentAddResult:
        self.require_available()
        info = lt.torrent_info(str(torrent_path))
        params = {"ti": info, "save_path": str(save_path)}
        handle = self.session.add_torrent(params)
        self._apply_add_options(handle, sequential_download, first_last_piece_priority)
        if paused:
            handle.pause()
        info_hash = str(handle.info_hash())
        self.handles[info_hash] = handle
        return self._result_from_info(info_hash, info)

    def restore_torrent_file(self, torrent_path: Path, save_path: Path, paused: bool = True) -> str:
        result = self.add_torrent_file(torrent_path, save_path, paused)
        return result.info_hash

    def add_magnet(
        self,
        magnet_uri: str,
        save_path: Path,
        paused: bool = False,
        sequential_download: bool = False,
        first_last_piece_priority: bool = False,
    ) -> TorrentAddResult:
        self.require_available()
        params = {"save_path": str(save_path)}
        handle = lt.add_magnet_uri(self.session, magnet_uri, params)
        self._apply_add_options(handle, sequential_download, first_last_piece_priority)
        if paused:
            handle.pause()
        info_hash = str(handle.info_hash())
        self.handles[info_hash] = handle
        return TorrentAddResult(info_hash=info_hash, name=display_text(handle.name() or "Magnet"), total_size=0, files=[], trackers=[])

    def restore_magnet(self, magnet_uri: str, save_path: Path, paused: bool = True) -> str:
        result = self.add_magnet(magnet_uri, save_path, paused)
        return result.info_hash

    def has_handle(self, info_hash: str) -> bool:
        return info_hash in self.handles

    def pause(self, info_hash: str) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            handle.pause()

    def resume(self, info_hash: str) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            handle.resume()

    def force_start(self, info_hash: str) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            try:
                handle.set_force_start(True)
            except Exception:
                pass
            handle.resume()

    def set_force_start(self, info_hash: str, enabled: bool = True) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            try:
                handle.set_force_start(enabled)
            except Exception:
                pass
            if enabled:
                handle.resume()

    def recheck(self, info_hash: str) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            handle.force_recheck()

    def reannounce(self, info_hash: str) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            handle.force_reannounce()

    def remove(self, info_hash: str, delete_files: bool = False) -> None:
        handle = self.handles.pop(info_hash, None)
        if handle and self.session:
            option = getattr(lt, "session", object)
            flags = 1 if delete_files else 0
            try:
                self.session.remove_torrent(handle, flags)
            except TypeError:
                self.session.remove_torrent(handle)

    def status(self, info_hash: str) -> dict[str, Any]:
        handle = self.handles.get(info_hash)
        if not handle:
            return {}
        st = handle.status()
        state = getattr(st, "state", None)
        status = "downloading"
        if getattr(st, "paused", False):
            status = "paused"
        elif getattr(st, "is_seeding", False):
            status = "seeding"
        elif float(getattr(st, "progress", 0.0)) >= 1.0:
            status = "finished"
        elif state == getattr(lt.torrent_status, "checking_files", object()):
            status = "checking"
        total = int(getattr(st, "total_wanted", 0) or getattr(st, "total", 0) or 0)
        download_rate = int(getattr(st, "download_rate", 0))
        downloaded = int(getattr(st, "total_done", 0))
        remaining = max(total - downloaded, 0)
        eta = int(remaining / download_rate) if download_rate > 0 else None
        error = ""
        try:
            error = str(st.errc.message()) if getattr(st, "errc", None) else ""
        except Exception:
            error = ""
        return {
            "status": status,
            "progress": float(getattr(st, "progress", 0.0)),
            "download_rate": download_rate,
            "upload_rate": int(getattr(st, "upload_rate", 0)),
            "downloaded": downloaded,
            "uploaded": int(getattr(st, "total_upload", 0)),
            "seeds": int(getattr(st, "num_seeds", 0)),
            "peers": int(getattr(st, "num_peers", 0)),
            "availability": float(getattr(st, "distributed_copies", 0.0)),
            "eta": eta,
            "state": str(state),
            "error": error,
            "total_size": total,
        }

    def poll_alerts(self) -> list[dict[str, Any]]:
        if self.session is None:
            return []
        alerts: list[Any] = []
        try:
            alerts = list(self.session.pop_alerts())
        except Exception:
            return []
        events = []
        for alert in alerts:
            name = type(alert).__name__
            handle = getattr(alert, "handle", None)
            info_hash = ""
            try:
                if handle:
                    info_hash = str(handle.info_hash())
            except Exception:
                info_hash = ""
            payload = {
                "type": name,
                "message": str(alert),
                "info_hash": info_hash,
            }
            if name in {"metadata_received_alert", "add_torrent_alert"}:
                try:
                    info = handle.torrent_file() if handle else None
                    if info:
                        payload["name"] = display_text(info.name())
                        payload["total_size"] = int(info.total_size()) if hasattr(info, "total_size") else 0
                        payload["files"] = self.files(info_hash)
                except Exception:
                    pass
            events.append(payload)
        return events

    def files(self, info_hash: str) -> list[dict[str, Any]]:
        handle = self.handles.get(info_hash)
        if not handle:
            return []
        try:
            info = handle.torrent_file()
            storage = info.files()
            priorities = list(handle.file_priorities())
            progresses = [0] * storage.num_files()
            try:
                progresses = list(handle.file_progress())
            except Exception:
                pass
            files = []
            for index in range(storage.num_files()):
                size = int(storage.file_size(index))
                done = int(progresses[index]) if index < len(progresses) else 0
                priority = int(priorities[index]) if index < len(priorities) else 1
                files.append(
                    {
                        "file_index": index,
                        "path": display_text(storage.file_path(index)),
                        "size": size,
                        "progress": (done / size) if size else 0.0,
                        "priority": priority,
                        "wanted": priority > 0,
                    }
                )
            return files
        except Exception:
            return []

    def trackers(self, info_hash: str) -> list[dict[str, Any]]:
        handle = self.handles.get(info_hash)
        if not handle:
            return []
        try:
            trackers = []
            for tracker in handle.trackers():
                trackers.append(
                    {
                        "url": display_text(getattr(tracker, "url", "")),
                        "status": "ativo" if getattr(tracker, "verified", False) else "pendente",
                        "message": display_text(getattr(tracker, "message", "") or ""),
                        "seeds": int(getattr(tracker, "scrape_complete", 0) or 0),
                        "peers": int(getattr(tracker, "scrape_incomplete", 0) or 0),
                    }
                )
            return trackers
        except Exception:
            return []

    def add_tracker(self, info_hash: str, url: str) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        try:
            handle.add_tracker({"url": url})
        except TypeError:
            try:
                handle.add_tracker(url)
            except Exception:
                pass
        except Exception:
            pass

    def remove_tracker(self, info_hash: str, url: str) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        try:
            trackers = [item for item in handle.trackers() if getattr(item, "url", "") != url]
            handle.replace_trackers(trackers)
        except Exception:
            pass

    def replace_tracker(self, info_hash: str, old_url: str, new_url: str) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        try:
            trackers = []
            for item in handle.trackers():
                if getattr(item, "url", "") == old_url:
                    try:
                        item.url = new_url
                        trackers.append(item)
                    except Exception:
                        trackers.append({"url": new_url})
                else:
                    trackers.append(item)
            handle.replace_trackers(trackers)
        except Exception:
            self.remove_tracker(info_hash, old_url)
            self.add_tracker(info_hash, new_url)

    def peers(self, info_hash: str) -> list[dict[str, Any]]:
        handle = self.handles.get(info_hash)
        if not handle:
            return []
        try:
            peers = []
            for peer in handle.get_peer_info():
                ip = getattr(peer, "ip", ("", 0))
                host, port = ip if isinstance(ip, tuple) else (display_text(ip), 0)
                peers.append(
                    {
                        "ip": display_text(host),
                        "port": int(port),
                        "client": display_text(getattr(peer, "client", "")),
                        "progress": float(getattr(peer, "progress", 0.0)),
                        "download_rate": int(getattr(peer, "down_speed", 0)),
                        "upload_rate": int(getattr(peer, "up_speed", 0)),
                        "flags": str(getattr(peer, "flags", "")),
                    }
                )
            return peers
        except Exception:
            return []

    def pieces(self, info_hash: str) -> list[int]:
        handle = self.handles.get(info_hash)
        if not handle:
            return []
        try:
            st = handle.status()
            pieces = getattr(st, "pieces", None)
            if pieces is not None:
                return [1 if bool(piece) else 0 for piece in pieces]
        except Exception:
            pass
        try:
            info = handle.torrent_file()
            count = int(info.num_pieces())
            return [1 if handle.have_piece(index) else 0 for index in range(count)]
        except Exception:
            return []

    def move_storage(self, info_hash: str, path: Path) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        try:
            handle.move_storage(str(path))
        except Exception:
            pass

    def set_torrent_limits(self, info_hash: str, download_limit: int | None = None, upload_limit: int | None = None) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        try:
            if download_limit is not None:
                handle.set_download_limit(int(download_limit))
            if upload_limit is not None:
                handle.set_upload_limit(int(upload_limit))
        except Exception:
            pass

    def set_sequential_download(self, info_hash: str, enabled: bool) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            self._call_handle_bool(handle, ["set_sequential_download", "set_sequential_download"], enabled)

    def set_first_last_piece_priority(self, info_hash: str, enabled: bool) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            self._call_handle_bool(handle, ["set_piece_deadline"], enabled)
            try:
                info = handle.torrent_file()
                count = int(info.num_pieces())
                if count:
                    deadline = 0 if enabled else 2147483647
                    handle.set_piece_deadline(0, deadline)
                    handle.set_piece_deadline(count - 1, deadline)
            except Exception:
                pass

    def set_super_seeding(self, info_hash: str, enabled: bool) -> None:
        handle = self.handles.get(info_hash)
        if handle:
            self._call_handle_bool(handle, ["super_seeding", "set_super_seeding"], enabled)

    def queue_top(self, info_hash: str) -> None:
        self._call_handle(info_hash, ["queue_position_top"])

    def queue_up(self, info_hash: str) -> None:
        self._call_handle(info_hash, ["queue_position_up"])

    def queue_down(self, info_hash: str) -> None:
        self._call_handle(info_hash, ["queue_position_down"])

    def queue_bottom(self, info_hash: str) -> None:
        self._call_handle(info_hash, ["queue_position_bottom"])

    def set_file_priority(self, info_hash: str, file_indexes: list[int], priority: int) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        for index in file_indexes:
            try:
                handle.file_priority(index, priority)
            except Exception:
                pass

    def set_speed_limits(self, download_limit: int, upload_limit: int) -> None:
        if not self.session:
            return
        try:
            self.session.set_download_rate_limit(download_limit)
            self.session.set_upload_rate_limit(upload_limit)
        except Exception:
            pass

    def _apply_add_options(self, handle, sequential_download: bool, first_last_piece_priority: bool) -> None:
        if sequential_download:
            self._call_handle_bool(handle, ["set_sequential_download"], True)
        if first_last_piece_priority:
            try:
                info = handle.torrent_file()
                count = int(info.num_pieces())
                if count:
                    handle.set_piece_deadline(0, 0)
                    handle.set_piece_deadline(count - 1, 0)
            except Exception:
                pass

    def _call_handle(self, info_hash: str, method_names: list[str]) -> None:
        handle = self.handles.get(info_hash)
        if not handle:
            return
        for method_name in method_names:
            method = getattr(handle, method_name, None)
            if method:
                try:
                    method()
                    return
                except Exception:
                    pass

    def _call_handle_bool(self, handle, method_names: list[str], enabled: bool) -> None:
        for method_name in method_names:
            method = getattr(handle, method_name, None)
            if method:
                try:
                    method(bool(enabled))
                    return
                except TypeError:
                    try:
                        method()
                        return
                    except Exception:
                        pass
                except Exception:
                    pass

    def save_state(self, path: Path) -> None:
        if self.session is None or lt is None:
            return
        try:
            entry = self.session.save_state()
            path.write_bytes(lt.bencode(entry))
        except Exception:
            pass

    def load_state(self, path: Path) -> None:
        if self.session is None or lt is None or not path.exists():
            return
        try:
            state = lt.bdecode(path.read_bytes())
            self.session.load_state(state)
        except Exception:
            pass

    def _result_from_info(self, info_hash: str, info: Any) -> TorrentAddResult:
        files = []
        total = 0
        try:
            storage = info.files()
            for index in range(storage.num_files()):
                path = display_text(storage.file_path(index))
                size = int(storage.file_size(index))
                total += size
                files.append({"file_index": index, "path": path, "size": size, "priority": 1, "wanted": True})
        except Exception:
            total = int(info.total_size()) if hasattr(info, "total_size") else 0
        trackers = []
        try:
            trackers = [display_text(tracker.url) for tracker in info.trackers()]
        except Exception:
            pass
        return TorrentAddResult(
            info_hash=info_hash,
            name=display_text(info.name()) if hasattr(info, "name") else "Torrent",
            total_size=total,
            files=files,
            trackers=trackers,
        )
