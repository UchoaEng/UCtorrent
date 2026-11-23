from __future__ import annotations

from pathlib import Path
from typing import Any

from uctorrent.app.core.event_bus import EventBus, event_bus
from uctorrent.app.core.torrent_session import TorrentSession
from uctorrent.app.database.db import get_session
from uctorrent.app.database.repositories import LogRepository, TorrentRepository, torrent_to_dict
from uctorrent.app.services.safety_service import SafetyService
from uctorrent.app.utils.constants import COMPLETED_DIR, SESSION_STATE_PATH


class TorrentManager:
    PERSISTED_STATUS_FIELDS = {
        "status",
        "progress",
        "download_rate",
        "upload_rate",
        "downloaded",
        "uploaded",
    }

    def __init__(self, config: dict[str, Any], safety: SafetyService | None = None, events: EventBus | None = None):
        self.config = config
        self.safety = safety or SafetyService()
        self.events = events or event_bus
        self.engine = TorrentSession(config.get("bittorrent", config))
        if hasattr(self.engine, "load_state"):
            self.engine.load_state(SESSION_STATE_PATH)
        self.runtime_status: dict[str, dict[str, Any]] = {}
        self.restore_session()

    def restore_session(self) -> None:
        session = get_session()
        try:
            repo = TorrentRepository(session)
            for torrent in repo.list():
                if not torrent.info_hash or self.engine.has_handle(torrent.info_hash):
                    continue
                try:
                    save_path = Path(torrent.save_path or COMPLETED_DIR)
                    if torrent.torrent_path and Path(torrent.torrent_path).exists():
                        self.engine.restore_torrent_file(Path(torrent.torrent_path), save_path, paused=torrent.status == "paused")
                        self._log_torrent_event(session, torrent.id, "Torrent restaurado na sessao.")
                    elif torrent.magnet_uri:
                        self.engine.restore_magnet(torrent.magnet_uri, save_path, paused=torrent.status == "paused")
                        self._log_torrent_event(session, torrent.id, "Magnet restaurado na sessao.")
                except Exception as exc:
                    torrent.status = "offline"
                    self._log_torrent_event(session, torrent.id, f"Nao foi possivel restaurar torrent: {exc}", level="WARNING")
            session.commit()
        finally:
            session.close()

    def list_torrents(self) -> list[dict[str, Any]]:
        self.sync_statuses()
        session = get_session()
        try:
            items = []
            for torrent in TorrentRepository(session).list():
                data = torrent_to_dict(torrent)
                if torrent.info_hash:
                    runtime = self.runtime_status.get(torrent.info_hash, {})
                    data["seeds"] = int(runtime.get("seeds") or 0)
                    data["peers"] = int(runtime.get("peers") or 0)
                    data["availability"] = float(runtime.get("availability") or 0.0)
                    data["eta"] = runtime.get("eta")
                    data["state"] = runtime.get("state", "")
                    data["error"] = runtime.get("error", "")
                else:
                    data["seeds"] = 0
                    data["peers"] = 0
                    data["availability"] = 0.0
                    data["eta"] = None
                items.append(data)
            return items
        finally:
            session.close()

    def backup_session_state(self) -> None:
        if hasattr(self.engine, "save_state"):
            self.engine.save_state(SESSION_STATE_PATH)

    def add_torrent_file(
        self,
        torrent_path: str | Path,
        save_path: str | Path | None = None,
        paused: bool = False,
        category: str | None = None,
        tags: list[str] | None = None,
        name: str | None = None,
        sequential_download: bool = False,
        first_last_piece_priority: bool = False,
    ) -> dict[str, Any]:
        path = Path(torrent_path)
        if path.suffix.lower() != ".torrent" or not path.exists():
            raise ValueError("Arquivo .torrent invalido ou inexistente.")
        target = Path(save_path or COMPLETED_DIR)
        target.mkdir(parents=True, exist_ok=True)
        result = self.engine.add_torrent_file(path, target, paused, sequential_download, first_last_piece_priority)
        return self._persist_added(
            result=result,
            magnet_uri=None,
            torrent_path=str(path),
            save_path=str(target),
            status="paused" if paused else "downloading",
            category=category,
            tags=tags or [],
            name=name,
            sequential_download=sequential_download,
            first_last_piece_priority=first_last_piece_priority,
        )

    def add_magnet(
        self,
        magnet_uri: str,
        save_path: str | Path | None = None,
        paused: bool = False,
        category: str | None = None,
        tags: list[str] | None = None,
        name: str | None = None,
        sequential_download: bool = False,
        first_last_piece_priority: bool = False,
    ) -> dict[str, Any]:
        self.safety.validate_magnet(magnet_uri)
        target = Path(save_path or COMPLETED_DIR)
        target.mkdir(parents=True, exist_ok=True)
        result = self.engine.add_magnet(magnet_uri, target, paused, sequential_download, first_last_piece_priority)
        return self._persist_added(
            result=result,
            magnet_uri=magnet_uri,
            torrent_path=None,
            save_path=str(target),
            status="paused" if paused else "metadata",
            category=category,
            tags=tags or [],
            name=name,
            sequential_download=sequential_download,
            first_last_piece_priority=first_last_piece_priority,
        )

    def pause(self, torrent_id: int) -> dict[str, Any]:
        return self._action(torrent_id, "paused", self.engine.pause)

    def resume(self, torrent_id: int) -> dict[str, Any]:
        return self._action(torrent_id, "downloading", self.engine.resume)

    def remove(self, torrent_id: int, delete_files: bool = False) -> None:
        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrent = repo.get(torrent_id)
            if torrent and torrent.info_hash:
                self.engine.remove(torrent.info_hash, delete_files)
            if torrent:
                action = "Torrent removido e arquivos solicitados para exclusao." if delete_files else "Torrent removido da lista."
                self._log_torrent_event(session, torrent_id, action)
            repo.delete(torrent_id)
            session.commit()
            self.events.publish("torrent_removed", {"id": torrent_id, "delete_files": delete_files})
            self.backup_session_state()
        finally:
            session.close()

    def sync_statuses(self) -> None:
        self._process_engine_alerts()
        session = get_session()
        try:
            repo = TorrentRepository(session)
            changed = False
            changed_ids = []
            for torrent in repo.list():
                if not torrent.info_hash:
                    continue
                status = self.engine.status(torrent.info_hash)
                if not status:
                    if torrent.status in {"downloading", "metadata", "checking", "queued", "seeding"}:
                        torrent.status = "offline"
                        self._log_torrent_event(session, torrent.id, "Torrent sem sessao ativa no libtorrent.", level="WARNING")
                        changed = True
                        changed_ids.append(torrent.id)
                    continue
                self.runtime_status[torrent.info_hash] = status
                for key, value in status.items():
                    if key in self.PERSISTED_STATUS_FIELDS:
                        if getattr(torrent, key) != value:
                            setattr(torrent, key, value)
                            changed = True
                            changed_ids.append(torrent.id)
                if torrent.downloaded and torrent.uploaded:
                    torrent.ratio = torrent.uploaded / max(torrent.downloaded, 1)
            if changed:
                session.commit()
                for torrent_id in sorted(set(changed_ids)):
                    self.events.publish("torrent_updated", {"id": torrent_id})
        finally:
            session.close()

    def set_category(self, torrent_id: int, category: str | None) -> dict[str, Any]:
        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrent = repo.get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if category:
                from uctorrent.app.database.repositories import CategoryRepository

                torrent.category = CategoryRepository(session).upsert(category)
            else:
                torrent.category = None
            self._log_torrent_event(session, torrent_id, f"Categoria alterada para {category or 'nenhuma'}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "category": category})
            return data
        finally:
            session.close()

    def set_tags(self, torrent_id: int, tags: list[str]) -> dict[str, Any]:
        from uctorrent.app.database.repositories import TagRepository

        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrent = repo.get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            tag_repo = TagRepository(session)
            torrent.tags = [tag_repo.create(tag.strip()) for tag in tags if tag.strip()]
            self._log_torrent_event(session, torrent_id, f"Tags alteradas para {', '.join(tags) or 'nenhuma'}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "tags": tags})
            return data
        finally:
            session.close()

    def _persist_added(
        self,
        result,
        magnet_uri,
        torrent_path,
        save_path,
        status,
        category,
        tags,
        name,
        sequential_download=False,
        first_last_piece_priority=False,
    ):
        session = get_session()
        try:
            repo = TorrentRepository(session)
            existing = repo.get_by_hash(result.info_hash)
            if existing:
                self._log_torrent_event(session, existing.id, "Torrent ja existia na lista.")
                session.commit()
                data = torrent_to_dict(existing)
                self.events.publish("torrent_updated", {"id": existing.id, "duplicate": True})
                return data
            torrent = repo.create(
                name=name or result.name,
                info_hash=result.info_hash,
                magnet_uri=magnet_uri,
                torrent_path=torrent_path,
                save_path=save_path,
                status=status,
                progress=0.0,
                total_size=result.total_size,
                sequential_download=bool(sequential_download),
                first_last_piece_priority=bool(first_last_piece_priority),
            )
            if result.files:
                repo.replace_files(torrent.id, result.files)
            if result.trackers:
                repo.replace_trackers(torrent.id, result.trackers)
            if category:
                from uctorrent.app.database.repositories import CategoryRepository

                torrent.category = CategoryRepository(session).upsert(category)
            if tags:
                from uctorrent.app.database.repositories import TagRepository

                tag_repo = TagRepository(session)
                torrent.tags = [tag_repo.create(tag) for tag in tags]
            self._log_torrent_event(session, torrent.id, "Torrent adicionado.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_added", data)
            self.backup_session_state()
            return data
        finally:
            session.close()

    def _action(self, torrent_id: int, status: str, engine_action) -> dict[str, Any]:
        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrent = repo.get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash:
                engine_action(torrent.info_hash)
            torrent.status = status
            self._log_torrent_event(session, torrent.id, f"Status alterado para {status}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "status": status})
            self.backup_session_state()
            return data
        finally:
            session.close()

    def force_start(self, torrent_id: int) -> dict[str, Any]:
        return self._action(torrent_id, "downloading", self.engine.force_start)

    def recheck(self, torrent_id: int) -> dict[str, Any]:
        return self._action(torrent_id, "checking", self.engine.recheck)

    def reannounce(self, torrent_id: int) -> dict[str, Any]:
        return self._action(torrent_id, "downloading", self.engine.reannounce)

    def batch_action(self, torrent_ids: list[int], action: str) -> list[dict[str, Any]]:
        return self.batch(torrent_ids, action)["results"]

    def batch(self, torrent_ids: list[int], action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        actions = {
            "pause": lambda torrent_id: self.pause(torrent_id),
            "resume": lambda torrent_id: self.resume(torrent_id),
            "force_start": lambda torrent_id: self.force_start(torrent_id),
            "recheck": lambda torrent_id: self.recheck(torrent_id),
            "reannounce": lambda torrent_id: self.reannounce(torrent_id),
            "remove": lambda torrent_id: self.remove(torrent_id, bool(params.get("delete_files", False))) or {"id": torrent_id},
            "set_category": lambda torrent_id: self.set_category(torrent_id, params.get("category")),
            "set_tags": lambda torrent_id: self.set_tags(torrent_id, list(params.get("tags") or [])),
            "set_location": lambda torrent_id: self.set_location(torrent_id, params["save_path"]),
            "set_limits": lambda torrent_id: self.set_torrent_limits(
                torrent_id,
                params.get("download_limit"),
                params.get("upload_limit"),
            ),
            "set_sequential_download": lambda torrent_id: self.set_sequential_download(torrent_id, bool(params.get("enabled", True))),
            "set_first_last_piece_priority": lambda torrent_id: self.set_first_last_piece_priority(torrent_id, bool(params.get("enabled", True))),
            "set_super_seeding": lambda torrent_id: self.set_super_seeding(torrent_id, bool(params.get("enabled", True))),
            "queue_top": lambda torrent_id: self.queue_action(torrent_id, "top"),
            "queue_up": lambda torrent_id: self.queue_action(torrent_id, "up"),
            "queue_down": lambda torrent_id: self.queue_action(torrent_id, "down"),
            "queue_bottom": lambda torrent_id: self.queue_action(torrent_id, "bottom"),
            "recover_sources": lambda torrent_id: self.recover_sources(torrent_id),
        }
        if action not in actions:
            raise ValueError(f"Acao em lote nao permitida: {action}")
        results = []
        failed = []
        for torrent_id in torrent_ids:
            try:
                results.append(actions[action](int(torrent_id)))
            except Exception as exc:
                failed.append({"id": torrent_id, "error": str(exc)})
        return {"ok": not failed, "results": results, "failed": failed}

    def get_torrent_details(self, torrent_id: int) -> dict[str, Any]:
        torrent = next((item for item in self.list_torrents() if item["id"] == torrent_id), None)
        if torrent is None:
            raise KeyError("Torrent nao encontrado.")
        torrent["files"] = self.get_files(torrent_id)
        torrent["trackers"] = self.get_trackers(torrent_id)
        torrent["peers_detail"] = self.get_peers(torrent_id)
        torrent["pieces"] = self.get_pieces(torrent_id)
        torrent["logs"] = self.get_torrent_logs(torrent_id)
        return torrent

    def get_files(self, torrent_id: int) -> list[dict[str, Any]]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                return []
            runtime = self.engine.files(torrent.info_hash) if torrent.info_hash else []
            if runtime:
                return runtime
            return [
                {
                    "id": item.id,
                    "file_index": item.file_index,
                    "path": item.path,
                    "size": item.size,
                    "progress": item.progress,
                    "priority": item.priority,
                    "wanted": item.wanted,
                }
                for item in torrent.files
            ]
        finally:
            session.close()

    def get_pieces(self, torrent_id: int) -> list[int]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None or not torrent.info_hash or not hasattr(self.engine, "pieces"):
                return []
            return self.engine.pieces(torrent.info_hash)
        finally:
            session.close()

    def get_trackers(self, torrent_id: int) -> list[dict[str, Any]]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                return []
            runtime = self.engine.trackers(torrent.info_hash) if torrent.info_hash else []
            if runtime:
                return runtime
            return [
                {"id": item.id, "url": item.url, "status": item.status, "message": item.message, "seeds": item.seeds, "peers": item.peers}
                for item in torrent.trackers
            ]
        finally:
            session.close()

    def get_peers(self, torrent_id: int) -> list[dict[str, Any]]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None or not torrent.info_hash:
                return []
            runtime = self.engine.peers(torrent.info_hash)
            if runtime:
                return runtime
            return [
                {
                    "ip": item.ip,
                    "port": item.port,
                    "client": item.client,
                    "progress": item.progress,
                    "download_rate": item.download_rate,
                    "upload_rate": item.upload_rate,
                    "flags": item.flags,
                }
                for item in torrent.peers
            ]
        finally:
            session.close()

    def get_torrent_logs(self, torrent_id: int, limit: int = 200) -> list[dict[str, Any]]:
        session = get_session()
        try:
            logs = LogRepository(session).list(limit=limit, scope=f"torrent:{torrent_id}")
            return [
                {
                    "id": item.id,
                    "level": item.level,
                    "scope": item.scope,
                    "message": item.message,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in logs
            ]
        finally:
            session.close()

    def set_file_priority(self, torrent_id: int, file_indexes: list[int], priority: int) -> None:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash:
                self.engine.set_file_priority(torrent.info_hash, file_indexes, priority)
            for item in torrent.files:
                if item.file_index in file_indexes:
                    item.priority = priority
                    item.wanted = priority > 0
            self._log_torrent_event(session, torrent_id, f"Prioridade de arquivos alterada para {priority}.")
            session.commit()
            self.events.publish("torrent_updated", {"id": torrent_id, "files": True})
        finally:
            session.close()

    def _log_torrent_event(self, session, torrent_id: int, message: str, level: str = "INFO") -> None:
        LogRepository(session).add(level, f"torrent:{torrent_id}", message)

    def rename(self, torrent_id: int, name: str) -> dict[str, Any]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).update(torrent_id, name=name)
            self._log_torrent_event(session, torrent_id, f"Torrent renomeado para {name}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "name": name})
            return data
        finally:
            session.close()

    def set_location(self, torrent_id: int, save_path: str | Path) -> dict[str, Any]:
        target = Path(save_path)
        target.mkdir(parents=True, exist_ok=True)
        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrent = repo.get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, "move_storage"):
                self.engine.move_storage(torrent.info_hash, target)
            torrent.save_path = str(target)
            self._log_torrent_event(session, torrent_id, f"Pasta de destino alterada para {target}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "save_path": str(target)})
            return data
        finally:
            session.close()

    def set_torrent_limits(
        self,
        torrent_id: int,
        download_limit: int | None = None,
        upload_limit: int | None = None,
    ) -> dict[str, Any]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, "set_torrent_limits"):
                self.engine.set_torrent_limits(torrent.info_hash, download_limit, upload_limit)
            if download_limit is not None:
                torrent.download_limit = int(download_limit)
            if upload_limit is not None:
                torrent.upload_limit = int(upload_limit)
            self._log_torrent_event(session, torrent_id, "Limites de velocidade alterados.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "limits": True})
            return data
        finally:
            session.close()

    def set_sequential_download(self, torrent_id: int, enabled: bool) -> dict[str, Any]:
        return self._set_bool_option(torrent_id, "sequential_download", enabled, "set_sequential_download")

    def set_first_last_piece_priority(self, torrent_id: int, enabled: bool) -> dict[str, Any]:
        return self._set_bool_option(torrent_id, "first_last_piece_priority", enabled, "set_first_last_piece_priority")

    def set_super_seeding(self, torrent_id: int, enabled: bool) -> dict[str, Any]:
        return self._set_bool_option(torrent_id, "super_seeding", enabled, "set_super_seeding")

    def _set_bool_option(self, torrent_id: int, field: str, enabled: bool, engine_method: str) -> dict[str, Any]:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, engine_method):
                getattr(self.engine, engine_method)(torrent.info_hash, enabled)
            setattr(torrent, field, bool(enabled))
            self._log_torrent_event(session, torrent_id, f"{field} alterado para {enabled}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, field: enabled})
            return data
        finally:
            session.close()

    def queue_action(self, torrent_id: int, action: str) -> dict[str, Any]:
        session = get_session()
        try:
            repo = TorrentRepository(session)
            torrents = repo.list()
            torrent = next((item for item in torrents if item.id == torrent_id), None)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash:
                method_name = f"queue_{action}"
                if hasattr(self.engine, method_name):
                    getattr(self.engine, method_name)(torrent.info_hash)
            ordered = [item for item in torrents if item.id != torrent_id]
            index = next((pos for pos, item in enumerate(torrents) if item.id == torrent_id), len(torrents) - 1)
            if action == "top":
                ordered.insert(0, torrent)
            elif action == "bottom":
                ordered.append(torrent)
            elif action == "up":
                ordered.insert(max(index - 1, 0), torrent)
            elif action == "down":
                ordered.insert(min(index + 1, len(ordered)), torrent)
            else:
                raise ValueError("Acao de fila invalida.")
            for pos, item in enumerate(ordered):
                item.queue_position = pos
            self._log_torrent_event(session, torrent_id, f"Fila alterada: {action}.")
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "queue": action})
            return data
        finally:
            session.close()

    def add_tracker(self, torrent_id: int, url: str) -> None:
        session = get_session()
        try:
            from uctorrent.app.database.models import Tracker

            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, "add_tracker"):
                self.engine.add_tracker(torrent.info_hash, url)
            if not any(item.url == url for item in torrent.trackers):
                torrent.trackers.append(Tracker(url=url))
            self._log_torrent_event(session, torrent_id, f"Tracker adicionado: {url}.")
            session.commit()
            self.events.publish("tracker_updated", {"id": torrent_id, "action": "added", "url": url})
        finally:
            session.close()

    def remove_tracker(self, torrent_id: int, url: str) -> None:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, "remove_tracker"):
                self.engine.remove_tracker(torrent.info_hash, url)
            torrent.trackers = [item for item in torrent.trackers if item.url != url]
            self._log_torrent_event(session, torrent_id, f"Tracker removido: {url}.")
            session.commit()
            self.events.publish("tracker_updated", {"id": torrent_id, "action": "removed", "url": url})
        finally:
            session.close()

    def edit_tracker(self, torrent_id: int, old_url: str, new_url: str) -> None:
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            if torrent.info_hash and hasattr(self.engine, "replace_tracker"):
                self.engine.replace_tracker(torrent.info_hash, old_url, new_url)
            for item in torrent.trackers:
                if item.url == old_url:
                    item.url = new_url
            self._log_torrent_event(session, torrent_id, f"Tracker editado: {old_url} -> {new_url}.")
            session.commit()
            self.events.publish("tracker_updated", {"id": torrent_id, "action": "edited", "old_url": old_url, "url": new_url})
        finally:
            session.close()

    def recover_sources(self, torrent_id: int) -> dict[str, Any]:
        trackers = list(self.config.get("bittorrent", {}).get("source_recovery_trackers") or [])
        added = 0
        session = get_session()
        try:
            torrent = TorrentRepository(session).get(torrent_id)
            if torrent is None:
                raise KeyError("Torrent nao encontrado.")
            existing = {item.url for item in torrent.trackers}
            from uctorrent.app.database.models import Tracker

            for url in trackers:
                if not url or url in existing:
                    continue
                if torrent.info_hash and hasattr(self.engine, "add_tracker"):
                    self.engine.add_tracker(torrent.info_hash, url)
                torrent.trackers.append(Tracker(url=url))
                added += 1
            if torrent.info_hash:
                try:
                    self.engine.reannounce(torrent.info_hash)
                    self.engine.resume(torrent.info_hash)
                except Exception:
                    pass
            torrent.status = "downloading"
            self._log_torrent_event(
                session,
                torrent_id,
                f"Recuperacao de fontes acionada: {added} tracker(s) publico(s) adicionados e reannounce solicitado.",
            )
            session.commit()
            data = torrent_to_dict(torrent)
            self.events.publish("torrent_updated", {"id": torrent_id, "recover_sources": True, "trackers_added": added})
            return data
        finally:
            session.close()

    def _process_engine_alerts(self) -> None:
        if not hasattr(self.engine, "poll_alerts"):
            return
        try:
            alerts = self.engine.poll_alerts()
        except Exception:
            return
        if not alerts:
            return
        session = get_session()
        try:
            repo = TorrentRepository(session)
            for alert in alerts:
                info_hash = alert.get("info_hash")
                torrent = repo.get_by_hash(info_hash) if info_hash else None
                if torrent:
                    if alert.get("name"):
                        torrent.name = alert["name"]
                    if alert.get("total_size"):
                        torrent.total_size = int(alert["total_size"])
                    if alert.get("files"):
                        repo.replace_files(torrent.id, alert["files"])
                    self._log_torrent_event(session, torrent.id, alert.get("message", "Evento do libtorrent."))
                    self.events.publish("metadata_received", {"id": torrent.id, "info_hash": info_hash})
                else:
                    self.events.publish("torrent_alert", alert)
            session.commit()
        finally:
            session.close()
