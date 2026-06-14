"""图像生成编排：调用生图服务并写入历史。"""

from __future__ import annotations

import logging

from app.config import settings
from app.schemas.draw import DrawResponse
from app.services.history_store import HistoryStoreError, add_history_entry
from app.services.image_generation import (
    ImageGenerationError,
    ImageGenerationNotConfiguredError,
    generate_image as create_image_from_prompt,
)

logger = logging.getLogger(__name__)


async def build_draw_response(
    prompt: str,
    *,
    display_prompt: str | None = None,
    width: int = 512,
    height: int = 512,
) -> DrawResponse:
    """根据提示词生成图像，并尽量写入历史记录。"""
    try:
        image_url, message = await create_image_from_prompt(prompt, width=width, height=height)
    except ImageGenerationNotConfiguredError as exc:
        raise exc
    except ImageGenerationError as exc:
        raise exc

    history_id: str | None = None
    history_saved = False
    response_image_url = image_url

    if settings.history_enabled and image_url:
        try:
            history_item = await add_history_entry(
                display_prompt=display_prompt or prompt,
                generation_prompt=prompt,
                image_url=image_url,
                message=message,
                width=width,
                height=height,
            )
            history_id = history_item.id
            history_saved = True
            response_image_url = history_item.image_url
        except HistoryStoreError as exc:
            logger.warning("历史记录保存失败: %s", exc)

    return DrawResponse(
        prompt=prompt,
        image_url=response_image_url,
        message=message,
        history_id=history_id,
        history_saved=history_saved,
    )
