"""生成历史持久化：JSON 元数据 + 本地图片文件。"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.history import HistoryItem
from app.services.image_fetch import download_image_as_data_url

_store_lock = asyncio.Lock()
_DATA_URL_PATTERN = re.compile(r"^data:(image/[^;]+);base64,(.+)$", re.DOTALL)
_MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}


class HistoryStoreError(Exception):
    """历史记录读写失败。"""


def _history_root() -> Path:
    if settings.history_dir:
        return Path(settings.history_dir).expanduser()
    return settings.backend_dir / "data" / "history"


def _history_file() -> Path:
    return _history_root() / "history.json"


def _images_dir() -> Path:
    return _history_root() / "images"


def _ensure_dirs() -> None:
    _images_dir().mkdir(parents=True, exist_ok=True)


def _public_image_url(item_id: str) -> str:
    return f"/api/history/{item_id}/image"


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    match = _DATA_URL_PATTERN.match(data_url.strip())
    if not match:
        raise HistoryStoreError("无效的图片 data URL")

    mime_type = match.group(1).lower()
    try:
        content = base64.b64decode(match.group(2), validate=True)
    except (ValueError, TypeError) as exc:
        raise HistoryStoreError("图片 data URL 解码失败") from exc

    if not content:
        raise HistoryStoreError("图片内容为空")

    return content, mime_type


def _extension_for_mime(mime_type: str) -> str:
    return _MIME_TO_EXT.get(mime_type.lower(), ".png")


async def _load_image_bytes(image_url: str) -> tuple[bytes, str]:
    if image_url.startswith("data:"):
        return _decode_data_url(image_url)

    if image_url.startswith("http://") or image_url.startswith("https://"):
        data_url = await download_image_as_data_url(image_url)
        return _decode_data_url(data_url)

    raise HistoryStoreError("不支持的图片 URL 格式")


def _read_items_unlocked() -> list[dict[str, Any]]:
    history_file = _history_file()
    if not history_file.exists():
        return []

    try:
        payload = json.loads(history_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HistoryStoreError("历史记录文件损坏") from exc

    items = payload.get("items", [])
    if not isinstance(items, list):
        raise HistoryStoreError("历史记录格式无效")

    return items


def _write_items_unlocked(items: list[dict[str, Any]]) -> None:
    _ensure_dirs()
    _history_file().write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _to_history_item(record: dict[str, Any]) -> HistoryItem:
    return HistoryItem(
        id=str(record["id"]),
        created_at=str(record["created_at"]),
        display_prompt=str(record.get("display_prompt", "")),
        generation_prompt=str(record.get("generation_prompt", "")),
        image_url=_public_image_url(str(record["id"])),
        message=str(record.get("message", "")),
        width=int(record.get("width", 512)),
        height=int(record.get("height", 512)),
    )


async def add_history_entry(
    *,
    display_prompt: str,
    generation_prompt: str,
    image_url: str,
    message: str = "",
    width: int = 512,
    height: int = 512,
) -> HistoryItem:
    """保存一条生成历史，并将图片写入本地。"""
    if not settings.history_enabled:
        raise HistoryStoreError("历史记录功能已关闭")

    item_id = uuid.uuid4().hex
    image_bytes, mime_type = await _load_image_bytes(image_url)
    extension = _extension_for_mime(mime_type)
    image_path = _images_dir() / f"{item_id}{extension}"

    record = {
        "id": item_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "display_prompt": display_prompt.strip() or generation_prompt.strip(),
        "generation_prompt": generation_prompt.strip(),
        "image_file": image_path.name,
        "message": message.strip(),
        "width": width,
        "height": height,
    }

    async with _store_lock:
        _ensure_dirs()
        image_path.write_bytes(image_bytes)
        items = _read_items_unlocked()
        items.insert(0, record)

        max_items = max(settings.history_max_items, 1)
        trimmed = items[:max_items]
        removed = items[max_items:]

        for old in removed:
            old_file = _images_dir() / str(old.get("image_file", ""))
            if old_file.is_file():
                old_file.unlink(missing_ok=True)

        _write_items_unlocked(trimmed)

    return _to_history_item(record)


async def list_history_entries(*, limit: int | None = None) -> list[HistoryItem]:
    """按时间倒序返回历史记录。"""
    if not settings.history_enabled:
        return []

    async with _store_lock:
        items = _read_items_unlocked()

    max_items = limit or settings.history_max_items
    return [_to_history_item(item) for item in items[:max_items]]


async def get_history_entry(item_id: str) -> HistoryItem | None:
    async with _store_lock:
        for record in _read_items_unlocked():
            if str(record.get("id")) == item_id:
                return _to_history_item(record)
    return None


def get_history_image_path(item_id: str) -> Path | None:
    """查找历史图片文件路径（同步，供路由读取）。"""
    if not _history_file().exists():
        return None

    try:
        items = _read_items_unlocked()
    except HistoryStoreError:
        return None

    for record in items:
        if str(record.get("id")) != item_id:
            continue
        image_file = str(record.get("image_file", ""))
        if not image_file:
            return None
        image_path = _images_dir() / image_file
        return image_path if image_path.is_file() else None

    return None


async def delete_history_entry(item_id: str) -> bool:
    """删除一条历史记录及对应图片。"""
    async with _store_lock:
        items = _read_items_unlocked()
        kept: list[dict[str, Any]] = []
        deleted = False

        for record in items:
            if str(record.get("id")) == item_id:
                deleted = True
                image_file = _images_dir() / str(record.get("image_file", ""))
                if image_file.is_file():
                    image_file.unlink(missing_ok=True)
                continue
            kept.append(record)

        if deleted:
            _write_items_unlocked(kept)

    return deleted
