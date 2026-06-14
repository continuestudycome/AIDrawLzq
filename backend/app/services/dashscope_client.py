"""阿里云百炼 DashScope 通用 HTTP 客户端。"""

from __future__ import annotations

import httpx

from app.config import settings


class DashScopeClientError(Exception):
    """DashScope API 调用失败。"""


def require_dashscope_api_key() -> str:
    api_key = settings.dashscope_api_key
    if not api_key:
        raise DashScopeClientError(
            "未配置 DASHSCOPE_API_KEY，请在 backend/.env 中设置后重启服务"
        )
    return api_key


def extract_api_error(payload: dict) -> str:
    code = str(payload.get("code", "")).strip()
    message = str(payload.get("message", "")).strip()
    error = payload.get("error")
    if isinstance(error, dict):
        error_message = str(error.get("message", "")).strip()
        if error_message:
            return error_message

    output = payload.get("output")
    if isinstance(output, dict):
        output_message = str(output.get("message", "")).strip()
        output_code = str(output.get("code", "")).strip()
        if output_message:
            if output_code:
                return f"{output_code}: {output_message}"
            return output_message

    if message:
        if code:
            return f"{code}: {message}"
        return message
    return "DashScope API 调用失败"


async def chat_completion(
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    extra_payload: dict | None = None,
    timeout_seconds: float | None = None,
) -> str:
    """调用 OpenAI 兼容接口，返回 assistant 文本内容。"""
    api_key = require_dashscope_api_key()
    url = f"{settings.dashscope_compatible_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model or settings.dashscope_chat_model,
        "messages": messages,
        "stream": False,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format
    if extra_payload:
        payload.update(extra_payload)

    timeout = timeout_seconds or settings.dashscope_request_timeout_seconds
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=True, http2=False) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise DashScopeClientError(f"DashScope 连接失败: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise DashScopeClientError(
            f"DashScope 返回格式无效 ({response.status_code}): {response.text.strip()}"
        ) from exc

    if response.status_code >= 400 or data.get("code"):
        raise DashScopeClientError(extract_api_error(data))

    choices = data.get("choices", [])
    if not choices:
        raise DashScopeClientError("DashScope 返回结果为空")

    message = choices[0].get("message", {})
    content = str(message.get("content", "")).strip()
    if not content:
        raise DashScopeClientError("DashScope 返回内容为空")
    return content
