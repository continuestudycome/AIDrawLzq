"""Stable Horde 免费图像生成：匿名 Key 即可使用，无需注册。"""

from __future__ import annotations

import asyncio

import httpx

from app.config import settings
from app.services.image_fetch import download_image_as_data_url


class StableHordeError(Exception):
    """Stable Horde 调用失败。"""


async def generate_stable_horde_data_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
    """提交 Stable Horde 任务，轮询完成后返回 data URL。"""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise StableHordeError("提示词不能为空")

    headers = {
        "apikey": settings.stable_horde_api_key,
        "Content-Type": "application/json",
    }
    payload: dict = {
        "prompt": cleaned_prompt,
        "params": {
            "width": max(64, min(width, 1024)),
            "height": max(64, min(height, 1024)),
            "steps": settings.stable_horde_steps,
        },
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
    }
    if settings.stable_horde_models_list:
        payload["models"] = settings.stable_horde_models_list

    base_url = settings.stable_horde_base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            submit = await client.post(f"{base_url}/generate/async", headers=headers, json=payload)
            if submit.status_code >= 400:
                detail = submit.text.strip() or submit.reason_phrase
                raise StableHordeError(f"提交生成任务失败 ({submit.status_code}): {detail}")

            job_id = submit.json().get("id")
            if not job_id:
                raise StableHordeError("Stable Horde 未返回任务 ID")

            poll_headers = {"apikey": settings.stable_horde_api_key}
            elapsed = 0.0
            while elapsed < settings.stable_horde_max_wait_seconds:
                check = await client.get(
                    f"{base_url}/generate/check/{job_id}",
                    headers=poll_headers,
                )
                if check.status_code >= 400:
                    detail = check.text.strip() or check.reason_phrase
                    raise StableHordeError(f"查询任务失败 ({check.status_code}): {detail}")

                check_data = check.json()
                if check_data.get("faulted"):
                    raise StableHordeError("Stable Horde 生成任务失败")
                if check_data.get("done"):
                    break

                await asyncio.sleep(settings.stable_horde_poll_interval)
                elapsed += settings.stable_horde_poll_interval
            else:
                raise StableHordeError(
                    f"免费队列等待超时（>{int(settings.stable_horde_max_wait_seconds)} 秒），请稍后重试"
                )

            status = await client.get(
                f"{base_url}/generate/status/{job_id}",
                headers=poll_headers,
            )
            if status.status_code >= 400:
                detail = status.text.strip() or status.reason_phrase
                raise StableHordeError(f"获取结果失败 ({status.status_code}): {detail}")

            generations = status.json().get("generations", [])
            if not generations:
                raise StableHordeError("Stable Horde 生成结果为空")

            image_url = generations[0].get("img")
            if not image_url:
                raise StableHordeError("Stable Horde 结果缺少图片地址")

            return await download_image_as_data_url(
                str(image_url),
                timeout_seconds=settings.image_timeout_seconds,
            )
    except StableHordeError:
        raise
    except httpx.RequestError as exc:
        raise StableHordeError(f"Stable Horde 连接失败: {exc}") from exc
    except ValueError as exc:
        raise StableHordeError(str(exc)) from exc
