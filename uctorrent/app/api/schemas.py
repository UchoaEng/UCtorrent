from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    username: str


class TorrentOut(BaseModel):
    id: int
    name: str
    info_hash: str | None = None
    magnet_uri: str | None = None
    save_path: str | None = None
    category: str | None = None
    status: str
    progress: float
    download_rate: int
    upload_rate: int
    total_size: int
    downloaded: int
    uploaded: int
    ratio: float
    tags: list[str] = Field(default_factory=list)


class AddMagnetRequest(BaseModel):
    magnet_uri: str
    save_path: str | None = None
    paused: bool = False
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    name: str | None = None
    sequential_download: bool = False
    first_last_piece_priority: bool = False


class BatchTorrentRequest(BaseModel):
    ids: list[int]
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class TorrentActionResponse(BaseModel):
    ok: bool = True
    torrent: dict[str, Any] | None = None


class RenameRequest(BaseModel):
    name: str


class SetLocationRequest(BaseModel):
    save_path: str


class SetLimitsRequest(BaseModel):
    download_limit: int | None = None
    upload_limit: int | None = None


class ToggleRequest(BaseModel):
    enabled: bool = True


class SetCategoryRequest(BaseModel):
    category: str | None = None


class SetTagsRequest(BaseModel):
    tags: list[str]


class FilePriorityRequest(BaseModel):
    file_indexes: list[int]
    priority: int


class CategoryIn(BaseModel):
    name: str
    save_path: str | None = None
    download_limit: int | None = None
    upload_limit: int | None = None
    ratio_limit: float | None = None
    seed_time_limit: int | None = None


class TagIn(BaseModel):
    name: str


class RssFeedIn(BaseModel):
    name: str
    url: str
    update_interval: int = 60
    enabled: bool = True


class RssRuleIn(BaseModel):
    name: str
    enabled: bool = True
    feed_id: int | None = None
    must_contain: str | None = None
    must_not_contain: str | None = None
    regex: str | None = None
    save_path: str | None = None
    category_id: int | None = None
    tags: str | None = None
    add_paused: bool = False
