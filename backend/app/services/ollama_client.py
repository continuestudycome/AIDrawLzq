"""Ollama 本地大模型：提示词优化。"""

from __future__ import annotations

import httpx

from app.config import settings


class OllamaError(Exception):
    """Ollama 调用失败。"""


OLLAMA_SYSTEM_PROMPT = (
    "你是 AI 绘图提示词专家。用户会输入简短的实体词、场景或画面描述（多为中文）。"
    "请将其扩展为适合 Stable Diffusion 的详细绘图提示词。"
    "必须只输出 JSON，包含两个字段："
    "display_cn（流畅完整的中文画面描述，给用户阅读；整合为自然语句，不要简单重复原文再堆砌）；"
    "prompt_en（纯英文绘图提示词，用于 AI 图像生成，不含任何中文）。"
    "要求：保留用户原意，补充主体细节、场景、风格、光影与画质关键词。"
)


async def chat_json(system_prompt: str, user_prompt: str) -> str:
    """调用 Ollama chat API，要求返回 JSON 文本。"""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": settings.ollama_temperature,
        },
    }

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


async def optimize_prompt_with_ollama(prompt: str) -> str:
    """将用户输入发送给 Ollama，返回模型输出的 JSON 文本。"""
    cleaned = prompt.strip()
    if not cleaned:
        raise OllamaError("提示词不能为空")

    user_message = (
        f"用户输入的实体/场景描述：{cleaned}\n"
        "请根据上述内容生成 display_cn 与 prompt_en。"
    )
    return await chat_json(OLLAMA_SYSTEM_PROMPT, user_message)
