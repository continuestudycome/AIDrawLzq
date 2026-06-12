"""图像生成服务：通过 OpenAI Images API 根据提示词生成图像。"""

from __future__ import annotations

import httpx

from app.config import settings


class ImageGenerationError(Exception):
    """图像生成调用失败。"""


class ImageGenerationNotConfiguredError(ImageGenerationError):
    """未配置图像生成所需的 API Key。"""


def resolve_image_size(width: int, height: int) -> str:
    """将请求宽高映射为 OpenAI Images API 支持的尺寸字符串。"""
    model = settings.image_model.lower()
    if model.startswith("dall-e-3"):
        if width > height:
            return "1792x1024"
        if height > width:
            return "1024x1792"
        return "1024x1024"

    size = max(width, height)
    if size <= 256:
        return "256x256"
    if size <= 512:
        return "512x512"
    return "1024x1024"


async def generate_image_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
    """根据提示词生成图像，返回可预览的图片 URL。"""
    api_key = settings.effective_image_api_key
    if not api_key:
        raise ImageGenerationNotConfiguredError(
            "未配置 OPENAI_API_KEY，请在 backend/.env 中设置后重启服务"
        )

    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ImageGenerationError("提示词不能为空")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, str | int] = {
        "model": settings.image_model,
        "prompt": cleaned_prompt,
        "n": 1,
        "size": resolve_image_size(width, height),
    }
    if settings.image_model.lower().startswith("dall-e-3"):
        payload["quality"] = settings.image_quality

    url = f"{settings.openai_base_url.rstrip('/')}/images/generations"

    try:
        async with httpx.AsyncClient(timeout=settings.image_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise ImageGenerationError(f"图像生成服务连接失败: {exc}") from exc

    if response.status_code == 401:
        raise ImageGenerationError("OPENAI_API_KEY 无效或已过期")
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise ImageGenerationError(f"图像生成失败 ({response.status_code}): {detail}")

    data = response.json().get("data", [])
    if not data:
        raise ImageGenerationError("图像生成结果为空")

    image_url = data[0].get("url")
    if not image_url:
        raise ImageGenerationError("图像生成结果缺少 url 字段")

    return str(image_url)
