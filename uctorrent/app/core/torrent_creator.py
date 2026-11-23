from __future__ import annotations

from pathlib import Path

from uctorrent.app.core.torrent_session import lt, TorrentEngineUnavailable


class TorrentCreator:
    def create(self, source: Path, output: Path, trackers: list[str], comment: str = "", private: bool = False) -> Path:
        if lt is None:
            raise TorrentEngineUnavailable("libtorrent nao esta instalado.")
        fs = lt.file_storage()
        lt.add_files(fs, str(source))
        creator = lt.create_torrent(fs)
        for tracker in trackers:
            creator.add_tracker(tracker)
        if comment:
            creator.set_comment(comment)
        if private:
            creator.set_priv(True)
        lt.set_piece_hashes(creator, str(source.parent if source.is_file() else source))
        output.write_bytes(lt.bencode(creator.generate()))
        return output

