"""Pollinations 免费图像生成：无需 API Key，通过 URL 生成图片。"""

from __future__ import annotations

from urllib.parse import quote

from app.config import settings


def clamp_dimension(value: int) -> int:
    return max(256, min(value, 1024))


def build_pollinations_image_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
    """根据提示词构建 Pollinations 图片 URL。"""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("提示词不能为空")

    encoded_prompt = quote(cleaned_prompt)
    base_url = settings.pollinations_base_url.rstrip("/")
    width_value = clamp_dimension(width)
    height_value = clamp_dimension(height)

    params = [
        f"width={width_value}",
        f"height={height_value}",
        "nologo=true",
    ]
    if settings.pollinations_model:
        params.append(f"model={quote(settings.pollinations_model)}")

    query = "&".join(params)
    return f"{base_url}/prompt/{encoded_prompt}?{query}"
