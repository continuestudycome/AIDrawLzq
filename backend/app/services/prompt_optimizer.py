"""提示词优化：将简短中文描述扩展为适合 AI 绘图的详细提示词。"""

from __future__ import annotations

import re

import httpx

from app.config import settings


class PromptOptimizerError(Exception):
    """提示词优化失败。"""


STYLE_HINTS: dict[str, str] = {
    "赛博朋克": "cyberpunk style, neon lights, futuristic city",
    "写实": "photorealistic, highly detailed",
    "卡通": "cartoon style, cute illustration",
    "动漫": "anime style, vibrant colors",
    "水彩": "watercolor painting, soft brush strokes",
    "油画": "oil painting, rich texture",
    "像素": "pixel art, retro game style",
    "科幻": "sci-fi, futuristic atmosphere",
    "奇幻": "fantasy, magical atmosphere",
    "古风": "traditional Chinese style, ancient aesthetic",
    "简约": "minimalist, clean composition",
    "暗黑": "dark mood, dramatic lighting",
    "可爱": "cute, adorable, kawaii",
}

SUBJECT_HINTS: dict[str, str] = {
    "猪": "a pig, farm animal",
    "猫": "a cat, feline",
    "狗": "a dog, canine",
    "鸡": "a chicken, rooster",
    "牛": "a cow, cattle",
    "羊": "a sheep, lamb",
    "马": "a horse, equine",
    "兔": "a rabbit, bunny",
    "龙": "a Chinese dragon, mythical creature",
    "鸟": "a bird, flying in the sky",
    "鱼": "a fish, underwater scene",
    "花": "beautiful flowers, botanical",
    "树": "a tree, nature landscape",
    "山": "mountain landscape, scenic view",
    "海": "ocean scene, waves and beach",
    "星空": "starry night sky, cosmos",
    "太阳": "sun, warm sunlight",
    "月亮": "moon, night scene",
    "人": "a person, portrait",
    "女孩": "a young girl, portrait",
    "男孩": "a young boy, portrait",
    "机器人": "a robot, mechanical design",
    "汽车": "a car, automotive",
    "房子": "a house, architecture",
    "城堡": "a castle, fantasy architecture",
}


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _collect_hints(text: str, hints: dict[str, str]) -> list[str]:
    matched: list[str] = []
    for keyword, english in hints.items():
        if keyword in text and english not in matched:
            matched.append(english)
    return matched


def optimize_prompt_with_rules(prompt: str) -> tuple[str, str]:
    """基于规则扩展提示词，返回 (optimized, message)。"""
    original = prompt.strip()
    if not original:
        raise PromptOptimizerError("提示词不能为空")

    style_parts = _collect_hints(original, STYLE_HINTS)
    subject_parts = _collect_hints(original, SUBJECT_HINTS)

    quality_suffix = "highly detailed, sharp focus, professional lighting, 8k quality"
    is_short = len(original) <= 12

    if _contains_chinese(original):
        english_parts = subject_parts + style_parts
        if is_short and not english_parts:
            english_parts = [f"detailed image of {original}"]

        if english_parts:
            english_clause = ", ".join(english_parts)
            optimized = f"{original}，{english_clause}, {quality_suffix}"
            message = "已补充英文描述与画质关键词，提升免费模型理解准确度"
        elif is_short:
            optimized = f"{original}，精细画面，主体清晰，{quality_suffix}"
            message = "已扩展简短描述并补充画质关键词"
        else:
            optimized = f"{original}, {quality_suffix}"
            message = "已补充画质与构图关键词"
    else:
        if is_short:
            optimized = f"a detailed image of {original}, {quality_suffix}"
            message = "已扩展英文短提示词"
        elif "highly detailed" not in original.lower():
            optimized = f"{original}, {quality_suffix}"
            message = "已补充画质关键词"
        else:
            optimized = original
            message = "提示词已较完整，仅做轻微整理"
            return optimized, message

    return optimized, message


async def _optimize_with_openai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.prompt_optimizer_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 AI 绘图提示词专家。将用户输入扩展为适合 Stable Diffusion 的详细提示词。"
                    "保留中文原意，并补充英文关键词、画面细节、风格与画质描述。"
                    "只输出优化后的提示词，不要解释。"
                ),
            },
            {"role": "user", "content": prompt.strip()},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=settings.prompt_optimizer_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise PromptOptimizerError(f"提示词优化服务连接失败: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise PromptOptimizerError(f"提示词优化失败 ({response.status_code}): {detail}")

    choices = response.json().get("choices", [])
    if not choices:
        raise PromptOptimizerError("提示词优化结果为空")

    content = str(choices[0].get("message", {}).get("content", "")).strip()
    if not content:
        raise PromptOptimizerError("提示词优化结果为空")

    return content


async def optimize_prompt(prompt: str) -> tuple[str, str, str]:
    """优化提示词，返回 (optimized, message, method)。"""
    original = prompt.strip()
    if not original:
        raise PromptOptimizerError("提示词不能为空")

    if settings.openai_api_key and settings.prompt_optimizer_use_openai:
        try:
            optimized = await _optimize_with_openai(original)
            return optimized, "已使用 AI 优化提示词（OpenAI）", "openai"
        except PromptOptimizerError:
            if not settings.prompt_optimizer_fallback_rules:
                raise

    optimized, message = optimize_prompt_with_rules(original)
    return optimized, message, "rules"
