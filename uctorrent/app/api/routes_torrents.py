from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from uctorrent.app.api.auth import require_auth
from uctorrent.app.api.schemas import (
    AddMagnetRequest,
    BatchTorrentRequest,
    FilePriorityRequest,
    RenameRequest,
    SetCategoryRequest,
    SetLimitsRequest,
    SetLocationRequest,
    SetTagsRequest,
    ToggleRequest,
)


def create_router(manager) -> APIRouter:
    router = APIRouter(prefix="/api/torrents", tags=["torrents"], dependencies=[Depends(require_auth)])

    @router.get("")
    def list_torrents():
        return manager.list_torrents()

    @router.post("/batch")
    def batch(payload: BatchTorrentRequest):
        try:
            return manager.batch(payload.ids, payload.action, payload.params)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/{torrent_id}")
    def torrent_details(torrent_id: int):
        try:
            return manager.get_torrent_details(torrent_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/add-file")
    async def add_file(payload: bytes = Body(...), filename: str = "upload.torrent", paused: bool = False):
        import tempfile
        from pathlib import Path

        suffix = Path(filename).suffix or ".torrent"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(payload)
            tmp_path = Path(tmp.name)
        try:
            return manager.add_torrent_file(tmp_path, paused=paused)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/add-magnet")
    def add_magnet(payload: AddMagnetRequest):
        try:
            return manager.add_magnet(**payload.model_dump())
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/{torrent_id}/pause")
    def pause(torrent_id: int):
        return {"ok": True, "torrent": manager.pause(torrent_id)}

    @router.post("/{torrent_id}/resume")
    def resume(torrent_id: int):
        return {"ok": True, "torrent": manager.resume(torrent_id)}

    @router.post("/{torrent_id}/force-start")
    def force_start(torrent_id: int):
        return {"ok": True, "torrent": manager.force_start(torrent_id)}

    @router.post("/{torrent_id}/remove")
    def remove(torrent_id: int, delete_files: bool = False):
        manager.remove(torrent_id, delete_files)
        return {"ok": True}

    @router.post("/{torrent_id}/recheck")
    def recheck(torrent_id: int):
        return {"ok": True, "torrent": manager.recheck(torrent_id)}

    @router.post("/{torrent_id}/reannounce")
    def reannounce(torrent_id: int):
        return {"ok": True, "torrent": manager.reannounce(torrent_id)}

    @router.post("/{torrent_id}/recover-sources")
    def recover_sources(torrent_id: int):
        try:
            return {"ok": True, "torrent": manager.recover_sources(torrent_id)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/set-location")
    def set_location(torrent_id: int, payload: SetLocationRequest):
        try:
            return manager.set_location(torrent_id, payload.save_path)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/rename")
    def rename(torrent_id: int, payload: RenameRequest):
        try:
            return manager.rename(torrent_id, payload.name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/set-category")
    def set_category(torrent_id: int, payload: SetCategoryRequest):
        return manager.set_category(torrent_id, payload.category)

    @router.post("/{torrent_id}/set-tags")
    def set_tags(torrent_id: int, payload: SetTagsRequest):
        try:
            return manager.set_tags(torrent_id, payload.tags)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/set-limits")
    def set_limits(torrent_id: int, payload: SetLimitsRequest):
        try:
            return manager.set_torrent_limits(torrent_id, payload.download_limit, payload.upload_limit)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/set-sequential-download")
    def set_sequential_download(torrent_id: int, payload: ToggleRequest):
        try:
            return manager.set_sequential_download(torrent_id, payload.enabled)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/{torrent_id}/set-first-last-piece-priority")
    def set_first_last_piece_priority(torrent_id: int, payload: ToggleRequest):
        try:
            return manager.set_first_last_piece_priority(torrent_id, payload.enabled)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{torrent_id}/files")
    def files(torrent_id: int):
        return manager.get_files(torrent_id)

    @router.post("/{torrent_id}/files/priority")
    def file_priority(torrent_id: int, payload: FilePriorityRequest):
        try:
            manager.set_file_priority(torrent_id, payload.file_indexes, payload.priority)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{torrent_id}/trackers")
    def trackers(torrent_id: int):
        return manager.get_trackers(torrent_id)

    @router.post("/{torrent_id}/trackers")
    def add_tracker(torrent_id: int, url: str):
        try:
            manager.add_tracker(torrent_id, url)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.put("/{torrent_id}/trackers")
    def edit_tracker(torrent_id: int, old_url: str, new_url: str):
        try:
            manager.edit_tracker(torrent_id, old_url, new_url)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/{torrent_id}/trackers")
    def delete_tracker(torrent_id: int, url: str):
        try:
            manager.remove_tracker(torrent_id, url)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{torrent_id}/peers")
    def peers(torrent_id: int):
        return manager.get_peers(torrent_id)

    @router.get("/{torrent_id}/pieces")
    def pieces(torrent_id: int):
        return manager.get_pieces(torrent_id)

    @router.get("/{torrent_id}/logs")
    def torrent_logs(torrent_id: int):
        return manager.get_torrent_logs(torrent_id)

    return router
