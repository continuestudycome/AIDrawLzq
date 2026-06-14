"""阿里云百炼 DashScope qwen-image-plus 文生图。"""

from __future__ import annotations

import asyncio
import time

import httpx

from app.config import settings
from app.services.image_fetch import download_image_as_data_url

_POLL_STATUSES = {"PENDING", "RUNNING"}


class DashScopeImageError(Exception):
    """DashScope 图像生成失败。"""


def resolve_dashscope_image_size(width: int, height: int) -> str:
    """将请求宽高映射为 qwen-image-plus 支持的分辨率。"""
    if width <= 0 or height <= 0:
        return settings.dashscope_image_size

    ratio = width / height
    if ratio > 1.3:
        return "1664*928"
    if ratio > 1.1:
        return "1472*1104"
    if ratio < 0.7:
        return "928*1664"
    if ratio < 0.9:
        return "1104*1472"
    return "1328*1328"


def _extract_api_error(payload: dict) -> str:
    code = str(payload.get("code", "")).strip()
    message = str(payload.get("message", "")).strip()
    output = payload.get("output")
    if isinstance(output, dict):
        output_code = str(output.get("code", "")).strip()
        output_message = str(output.get("message", "")).strip()
        if output_message:
            if output_code:
                return f"{output_code}: {output_message}"
            return output_message
    if message:
        if code:
            return f"{code}: {message}"
        return message
    return "DashScope 图像生成失败"


async def generate_dashscope_image_data_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
    """提交 qwen-image-plus 异步任务，轮询完成后返回 data URL。"""
    api_key = settings.dashscope_api_key
    if not api_key:
        raise DashScopeImageError(
            "未配置 DASHSCOPE_API_KEY，请在 backend/.env 中设置后重启服务"
        )

    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise DashScopeImageError("提示词不能为空")

    base_url = settings.dashscope_base_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": settings.dashscope_image_model,
        "input": {"prompt": cleaned_prompt},
        "parameters": {
            "negative_prompt": settings.dashscope_negative_prompt,
            "size": resolve_dashscope_image_size(width, height),
            "n": 1,
            "prompt_extend": settings.dashscope_prompt_extend,
            "watermark": settings.dashscope_watermark,
        },
    }

    timeout = httpx.Timeout(
        settings.dashscope_request_timeout_seconds,
        connect=settings.dashscope_connect_timeout_seconds,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=True, http2=False) as client:
            submit = await client.post(
                f"{base_url}/services/aigc/text2image/image-synthesis",
                headers=headers,
                json=payload,
            )
            submit_data = submit.json()
            if submit.status_code >= 400 or submit_data.get("code"):
                raise DashScopeImageError(_extract_api_error(submit_data))

            task_id = submit_data.get("output", {}).get("task_id")
            if not task_id:
                raise DashScopeImageError("DashScope 未返回 task_id")

            deadline = time.monotonic() + settings.dashscope_max_wait_seconds
            poll_headers = {"Authorization": f"Bearer {api_key}"}

            while time.monotonic() < deadline:
                status_resp = await client.get(
                    f"{base_url}/tasks/{task_id}",
                    headers=poll_headers,
                )
                status_data = status_resp.json()
                if status_resp.status_code >= 400 or status_data.get("code"):
                    raise DashScopeImageError(_extract_api_error(status_data))

                output = status_data.get("output", {})
                task_status = str(output.get("task_status", "")).upper()
                if task_status == "SUCCEEDED":
                    results = output.get("results", [])
                    if not results:
                        raise DashScopeImageError("DashScope 生成结果为空")
                    image_url = results[0].get("url")
                    if not image_url:
                        raise DashScopeImageError("DashScope 结果缺少图片 URL")
                    return await download_image_as_data_url(
                        str(image_url),
                        timeout_seconds=settings.image_timeout_seconds,
                    )

                if task_status not in _POLL_STATUSES:
                    if task_status in {"FAILED", "CANCELED", "UNKNOWN"}:
                        raise DashScopeImageError(_extract_api_error(status_data))
                    raise DashScopeImageError(f"未知任务状态: {task_status}")

                await asyncio.sleep(settings.dashscope_poll_interval)

            raise DashScopeImageError(
                f"DashScope 任务等待超时（>{int(settings.dashscope_max_wait_seconds)} 秒），请稍后重试"
            )
    except DashScopeImageError:
        raise
    except httpx.RequestError as exc:
        raise DashScopeImageError(f"DashScope 连接失败: {exc}") from exc
    except ValueError as exc:
        raise DashScopeImageError(str(exc)) from exc
