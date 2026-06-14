"""图像生成服务：支持 OpenAI DALL·E、Stable Horde 与 Pollinations。"""

from __future__ import annotations

import httpx

from app.config import settings
from app.services.image_fetch import download_image_as_data_url
from app.services.pollinations_image import build_pollinations_image_url
from app.services.stable_horde_image import StableHordeError, generate_stable_horde_data_url


class ImageGenerationError(Exception):
    """图像生成调用失败。"""


class ImageGenerationNotConfiguredError(ImageGenerationError):
    """未配置图像生成所需的 API Key。"""


def resolve_openai_image_size(width: int, height: int) -> str:
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


def resolve_image_provider() -> str:
    """解析当前应使用的图像生成提供方。"""
    provider = settings.image_provider.lower().strip()
    if provider == "openai":
        if not settings.effective_image_api_key:
            raise ImageGenerationNotConfiguredError(
                "IMAGE_PROVIDER=openai 但未配置 OPENAI_API_KEY，请在 backend/.env 中设置"
            )
        return "openai"
    if provider in {"pollinations", "stablehorde", "free"}:
        return provider

    if settings.effective_image_api_key:
        return "openai"
    return "free"


async def _generate_openai_image_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
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
        "size": resolve_openai_image_size(width, height),
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


async def _try_pollinations_data_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str | None:
    try:
        remote_url = build_pollinations_image_url(prompt, width=width, height=height)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(remote_url)
        if response.status_code >= 400:
            return None
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return None
        return await download_image_as_data_url(remote_url, timeout_seconds=30.0)
    except (httpx.RequestError, ValueError):
        return None


async def _generate_free_image_data_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> tuple[str, str]:
    provider = settings.image_provider.lower().strip()

    if provider == "pollinations":
        image_url = await _try_pollinations_data_url(prompt, width=width, height=height)
        if image_url:
            return image_url, "图像已生成（Pollinations）"
        raise ImageGenerationError(
            "Pollinations 服务不可用（可能已需付费 402），请改用 IMAGE_PROVIDER=stablehorde"
        )

    try:
        image_url = await generate_stable_horde_data_url(prompt, width=width, height=height)
        return image_url, "图像已生成（Stable Horde 免费服务，排队可能需要 1-3 分钟）"
    except StableHordeError as exc:
        raise ImageGenerationError(
            f"Stable Horde 生图失败：{exc}。"
            "可尝试：1) 稍后重试 2) 清空 STABLE_HORDE_MODELS 使用任意可用模型 "
            "3) 注册专属 Key 提升优先级 4) 配置 OpenAI DALL·E"
        ) from exc


async def generate_image(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> tuple[str, str]:
    """根据提示词生成图像，返回 (image_url, message)。"""
    provider = resolve_image_provider()

    if provider == "openai":
        image_url = await _generate_openai_image_url(prompt, width=width, height=height)
        return image_url, "图像已生成（OpenAI DALL·E）"

    return await _generate_free_image_data_url(prompt, width=width, height=height)
