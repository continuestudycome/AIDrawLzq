"""提示词优化：生成中文展示版与英文绘图版。"""

from __future__ import annotations

import json
import re

import httpx

from app.config import settings


class PromptOptimizerError(Exception):
    """提示词优化失败。"""


STYLE_HINTS_EN: dict[str, str] = {
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

STYLE_HINTS_CN: dict[str, str] = {
    "赛博朋克": "赛博朋克风格，霓虹灯光，未来都市",
    "写实": "写实风格，高度细节",
    "卡通": "卡通风格，可爱插画",
    "动漫": "动漫风格，色彩鲜明",
    "水彩": "水彩画风，柔和笔触",
    "油画": "油画质感，厚重纹理",
    "像素": "像素艺术，复古游戏风",
    "科幻": "科幻氛围，未来感",
    "奇幻": "奇幻风格，魔法氛围",
    "古风": "中国古风，古典美学",
    "简约": "简约构图，画面干净",
    "暗黑": "暗黑氛围，戏剧光影",
    "可爱": "可爱风格，萌系",
}

SUBJECT_HINTS_EN: dict[str, str] = {
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

SUBJECT_HINTS_CN: dict[str, str] = {
    "猪": "猪，农场动物",
    "猫": "猫",
    "狗": "狗",
    "鸡": "鸡",
    "牛": "牛",
    "羊": "羊",
    "马": "马",
    "兔": "兔子",
    "龙": "中国龙，神话生物",
    "鸟": "鸟，飞翔于天空",
    "鱼": "鱼，水下场景",
    "花": "鲜花，植物",
    "树": "树木，自然风景",
    "山": "山峦风景",
    "海": "海洋，海浪与沙滩",
    "星空": "星空，宇宙",
    "太阳": "太阳，温暖阳光",
    "月亮": "月亮，夜晚场景",
    "人": "人物肖像",
    "女孩": "女孩肖像",
    "男孩": "男孩肖像",
    "机器人": "机器人，机械设计",
    "汽车": "汽车",
    "房子": "房屋建筑",
    "城堡": "城堡，奇幻建筑",
}

QUALITY_CN = "精细画面，主体清晰，专业光影，高清画质"
QUALITY_EN = "highly detailed, sharp focus, professional lighting, 8k quality"


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _collect_hints(text: str, hints: dict[str, str]) -> list[str]:
    matched: list[str] = []
    for keyword, phrase in hints.items():
        if keyword in text and phrase not in matched:
            matched.append(phrase)
    return matched


def _join_unique(parts: list[str], separator: str) -> str:
    return separator.join(dict.fromkeys(part.strip() for part in parts if part.strip()))


def optimize_prompt_with_rules(prompt: str) -> tuple[str, str, str]:
    """基于规则扩展提示词，返回 (optimized_cn, optimized_en, message)。"""
    original = prompt.strip()
    if not original:
        raise PromptOptimizerError("提示词不能为空")

    style_cn = _collect_hints(original, STYLE_HINTS_CN)
    subject_cn = _collect_hints(original, SUBJECT_HINTS_CN)
    style_en = _collect_hints(original, STYLE_HINTS_EN)
    subject_en = _collect_hints(original, SUBJECT_HINTS_EN)
    is_short = len(original) <= 12

    if _contains_chinese(original):
        cn_parts = [original]
        cn_parts.extend(subject_cn)
        cn_parts.extend(style_cn)
        optimized_cn = f"{_join_unique(cn_parts, '，')}，{QUALITY_CN}"

        en_parts = subject_en + style_en
        if is_short and not en_parts:
            en_parts = [f"detailed image of {original}"]
        optimized_en = f"{_join_unique(en_parts, ', ')}, {QUALITY_EN}"
        message = "已生成中文说明与英文绘图提示词，生成图像时将使用英文版本"
    else:
        if is_short:
            optimized_en = f"a detailed image of {original}, {QUALITY_EN}"
            message = "已扩展英文绘图提示词"
        elif "highly detailed" not in original.lower():
            optimized_en = f"{original}, {QUALITY_EN}"
            message = "已补充英文画质关键词"
        else:
            optimized_en = original
            message = "英文提示词已较完整"

        optimized_cn = optimized_en
        if message != "英文提示词已较完整":
            message = f"{message}（输入为英文，界面显示与绘图均使用英文）"

    return optimized_cn, optimized_en, message


def _parse_openai_dual_prompt(content: str) -> tuple[str, str]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PromptOptimizerError("AI 返回格式无效，无法解析中英文提示词") from exc

    display_cn = str(data.get("display_cn", "")).strip()
    prompt_en = str(data.get("prompt_en", "")).strip()

    if not display_cn or not prompt_en:
        raise PromptOptimizerError("AI 未返回完整的中英文提示词")

    return display_cn, prompt_en


async def _optimize_with_openai(prompt: str) -> tuple[str, str]:
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
                    "必须输出 JSON，且只输出 JSON，包含两个字段："
                    "display_cn（中文描述，给用户阅读，保留中文原意并补充画面细节、风格与画质）；"
                    "prompt_en（纯英文绘图提示词，用于 AI 图像生成，不含任何中文）。"
                ),
            },
            {"role": "user", "content": prompt.strip()},
        ],
        "temperature": 0.7,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
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

    return _parse_openai_dual_prompt(content)


async def optimize_prompt(prompt: str) -> tuple[str, str, str, str]:
    """优化提示词，返回 (optimized_cn, optimized_en, message, method)。"""
    original = prompt.strip()
    if not original:
        raise PromptOptimizerError("提示词不能为空")

    if settings.openai_api_key and settings.prompt_optimizer_use_openai:
        try:
            optimized_cn, optimized_en = await _optimize_with_openai(original)
            return (
                optimized_cn,
                optimized_en,
                "已使用 AI 生成中文说明与英文绘图提示词",
                "openai",
            )
        except PromptOptimizerError:
            if not settings.prompt_optimizer_fallback_rules:
                raise

    optimized_cn, optimized_en, message = optimize_prompt_with_rules(original)
    return optimized_cn, optimized_en, message, "rules"
