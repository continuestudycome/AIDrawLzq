"""将远程图片下载为 data URL，便于前端稳定预览。"""

from __future__ import annotations

import base64

import httpx


async def download_image_as_data_url(
    image_url: str,
    *,
    timeout_seconds: float = 60.0,
) -> str:
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(image_url)

    if response.status_code >= 400:
        raise ValueError(f"图片下载失败 ({response.status_code})")

    content_type = response.headers.get("content-type", "image/png").split(";")[0]
    if not content_type.startswith("image/"):
        raise ValueError("响应不是有效图片")

    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"
