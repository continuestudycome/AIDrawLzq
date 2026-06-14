"""语音识别服务：支持本地 Whisper 与 OpenAI Whisper API。"""

from __future__ import annotations

import httpx

from app.config import settings
from app.services.local_speech_recognition import (
    LocalSpeechRecognitionError,
    transcribe_local_audio,
)


class SpeechRecognitionError(Exception):
    """语音识别调用失败。"""


class SpeechRecognitionNotConfiguredError(SpeechRecognitionError):
    """未配置语音识别所需的 API Key。"""


async def _transcribe_openai_audio(
    audio_bytes: bytes,
    *,
    filename: str = "recording.webm",
    content_type: str | None = None,
) -> tuple[str, float | None]:
    if not settings.openai_api_key:
        raise SpeechRecognitionNotConfiguredError(
            "未配置 OPENAI_API_KEY，请在 backend/.env 中设置后重启服务"
        )

    if not audio_bytes:
        raise SpeechRecognitionError("音频内容为空")

    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    files = {
        "file": (
            filename,
            audio_bytes,
            content_type or "application/octet-stream",
        )
    }
    data: dict[str, str] = {"model": settings.speech_model}
    if settings.speech_language:
        data["language"] = settings.speech_language

    url = f"{settings.openai_base_url.rstrip('/')}/audio/transcriptions"

    try:
        async with httpx.AsyncClient(timeout=settings.speech_timeout_seconds) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
    except httpx.RequestError as exc:
        raise SpeechRecognitionError(f"语音识别服务连接失败: {exc}") from exc

    if response.status_code == 401:
        raise SpeechRecognitionError("OPENAI_API_KEY 无效或已过期")
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise SpeechRecognitionError(f"语音识别失败 ({response.status_code}): {detail}")

    payload = response.json()
    text = str(payload.get("text", "")).strip()
    if not text:
        raise SpeechRecognitionError("语音识别结果为空，请重新录音")

    return text, None


def resolve_speech_provider() -> str:
    provider = settings.speech_provider.lower().strip()
    if provider in {"local", "openai"}:
        return provider
    if provider == "auto":
        return "openai" if settings.openai_api_key else "local"
    if settings.openai_api_key:
        return "openai"
    return "local"


async def transcribe_audio(
    audio_bytes: bytes,
    *,
    filename: str = "recording.webm",
    content_type: str | None = None,
) -> tuple[str, float | None]:
    """将音频识别为文本，返回 (text, confidence)。"""
    provider = resolve_speech_provider()

    if provider == "openai":
        return await _transcribe_openai_audio(
            audio_bytes,
            filename=filename,
            content_type=content_type,
        )

    try:
        return await transcribe_local_audio(audio_bytes, filename=filename)
    except LocalSpeechRecognitionError as exc:
        raise SpeechRecognitionError(str(exc)) from exc
