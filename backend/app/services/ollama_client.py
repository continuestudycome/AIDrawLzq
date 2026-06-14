"""Ollama 本地大模型：提示词优化。"""

from __future__ import annotations

import httpx

from app.config import settings


class OllamaError(Exception):
    """Ollama 调用失败。"""


OLLAMA_SYSTEM_PROMPT = (
    "你是 AI 绘图提示词专家。将用户的简短实体词或场景描述扩展为 Stable Diffusion 提示词。"
    '只输出 JSON：{"display_cn":"流畅中文画面描述","prompt_en":"纯英文绘图提示词"}。'
    "保留原意，补充主体、场景、风格、光影与画质词；整合成自然语句，勿重复堆砌原文。"
)

_prompt_cache: dict[str, str] = {}


def _build_ollama_options() -> dict[str, float | int]:
    return {
        "temperature": settings.ollama_temperature,
        "num_predict": settings.ollama_num_predict,
        "num_ctx": settings.ollama_num_ctx,
    }


def _build_chat_payload(messages: list[dict[str, str]]) -> dict:
    return {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "keep_alive": settings.ollama_keep_alive,
        "options": _build_ollama_options(),
    }


async def _post_chat(payload: dict) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(url, json=payload)
    except httpx.ConnectError:
        raise OllamaError(
            "无法连接 Ollama，请确认已启动服务（ollama serve）且地址正确："
            f"{settings.ollama_base_url}"
        ) from None
    except httpx.RequestError as exc:
        raise OllamaError(f"Ollama 连接失败: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        if response.status_code == 404 and "model" in detail.lower():
            raise OllamaError(
                f"Ollama 模型不存在: {settings.ollama_model}，请先执行 ollama pull {settings.ollama_model}"
            )
        raise OllamaError(f"Ollama 请求失败 ({response.status_code}): {detail}")

    message = response.json().get("message", {})
    content = str(message.get("content", "")).strip()
    if not content:
        raise OllamaError("Ollama 返回内容为空")

    return content


async def chat_json(system_prompt: str, user_prompt: str) -> str:
    """调用 Ollama chat API，要求返回 JSON 文本。"""
    payload = _build_chat_payload(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return await _post_chat(payload)


async def warmup_ollama_model() -> None:
    """后端启动时预加载模型，避免首次优化等待过久。"""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
        "keep_alive": settings.ollama_keep_alive,
        "options": {"num_predict": 1, "num_ctx": 512},
    }

    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


def clear_prompt_cache() -> None:
    _prompt_cache.clear()


async def optimize_prompt_with_ollama(prompt: str) -> str:
    """将用户输入发送给 Ollama，返回模型输出的 JSON 文本。"""
    cleaned = prompt.strip()
    if not cleaned:
        raise OllamaError("提示词不能为空")

    cache_key = cleaned.casefold()
    if settings.ollama_cache_enabled and cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    user_message = f"用户输入：{cleaned}"
    content = await chat_json(OLLAMA_SYSTEM_PROMPT, user_message)

    if settings.ollama_cache_enabled:
        if len(_prompt_cache) >= settings.ollama_cache_max_items:
            oldest_key = next(iter(_prompt_cache))
            _prompt_cache.pop(oldest_key, None)
        _prompt_cache[cache_key] = content

    return content
