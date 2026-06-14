"""将远程图片下载为 data URL，便于前端稳定预览。"""

from __future__ import annotations

import asyncio
import base64

import httpx

_RETRY_BACKOFF_SECONDS = (2.0, 4.0, 8.0)


async def download_image_as_data_url(
    image_url: str,
    *,
    timeout_seconds: float = 60.0,
    max_attempts: int = 4,
) -> str:
    timeout = httpx.Timeout(timeout_seconds, connect=min(30.0, timeout_seconds))
    last_error: httpx.RequestError | None = None

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                trust_env=True,
                http2=False,
            ) as client:
                response = await client.get(image_url)
            break
        except httpx.RequestError as exc:
            last_error = exc
            if attempt >= max_attempts - 1:
                raise ValueError(f"图片下载连接失败: {exc}") from exc
            await asyncio.sleep(_RETRY_BACKOFF_SECONDS[min(attempt, len(_RETRY_BACKOFF_SECONDS) - 1)])
    else:
        raise ValueError(f"图片下载连接失败: {last_error}")

    if response.status_code >= 400:
        raise ValueError(f"图片下载失败 ({response.status_code})")

    content_type = response.headers.get("content-type", "image/png").split(";")[0]
    if not content_type.startswith("image/"):
        raise ValueError("响应不是有效图片")

    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"
