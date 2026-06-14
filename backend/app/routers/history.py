from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.history import HistoryListResponse
from app.services.history_store import (
    HistoryStoreError,
    delete_history_entry,
    get_history_image_path,
    list_history_entries,
)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
async def list_history(limit: int = 50) -> HistoryListResponse:
    """获取生成历史列表（按时间倒序）。"""
    if not settings.history_enabled:
        return HistoryListResponse(items=[], total=0)

    safe_limit = max(1, min(limit, settings.history_max_items))
    try:
        items = await list_history_entries(limit=safe_limit)
    except HistoryStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return HistoryListResponse(items=items, total=len(items))


@router.get("/{item_id}/image")
async def get_history_image(item_id: str) -> FileResponse:
    """返回历史记录中的图片文件。"""
    image_path = get_history_image_path(item_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="历史图片不存在")

    media_type = _guess_media_type(image_path)
    return FileResponse(image_path, media_type=media_type)


@router.delete("/{item_id}")
async def remove_history_item(item_id: str) -> dict[str, bool]:
    """删除一条历史记录。"""
    if not settings.history_enabled:
        raise HTTPException(status_code=503, detail="历史记录功能已关闭")

    try:
        deleted = await delete_history_entry(item_id)
    except HistoryStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="历史记录不存在")

    return {"ok": True}


def _guess_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    return mapping.get(suffix, "application/octet-stream")
