"""阿里云百炼 DashScope 语音识别（qwen3-asr-flash）。"""

from __future__ import annotations

import base64
from pathlib import Path

from app.config import settings
from app.services.dashscope_client import DashScopeClientError, chat_completion


class DashScopeSpeechError(Exception):
    """DashScope 语音识别失败。"""


_MIME_BY_SUFFIX = {
    ".webm": "audio/webm",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".mpeg": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".aac": "audio/aac",
}


def _guess_audio_mime(filename: str, content_type: str | None) -> str:
    if content_type:
        mime = content_type.split(";", 1)[0].strip().lower()
        if mime.startswith("audio/"):
            return mime
    suffix = Path(filename).suffix.lower()
    return _MIME_BY_SUFFIX.get(suffix, "audio/webm")


def _build_audio_data_uri(
    audio_bytes: bytes,
    *,
    filename: str,
    content_type: str | None,
) -> str:
    mime_type = _guess_audio_mime(filename, content_type)
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


async def transcribe_dashscope_audio(
    audio_bytes: bytes,
    *,
    filename: str = "recording.webm",
    content_type: str | None = None,
) -> tuple[str, float | None]:
    """将音频识别为文本，返回 (text, confidence)。"""
    if not audio_bytes:
        raise DashScopeSpeechError("音频内容为空")

    data_uri = _build_audio_data_uri(
        audio_bytes,
        filename=filename,
        content_type=content_type,
    )
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {"data": data_uri},
                }
            ],
        }
    ]

    try:
        text = await chat_completion(
            messages,
            model=settings.dashscope_speech_model,
            timeout_seconds=settings.speech_timeout_seconds,
            extra_payload={
                "asr_options": {
                    "enable_itn": settings.dashscope_asr_enable_itn,
                }
            },
        )
    except DashScopeClientError as exc:
        raise DashScopeSpeechError(str(exc)) from exc

    cleaned = text.strip()
    if not cleaned:
        raise DashScopeSpeechError("语音识别结果为空，请重新录音")

    return cleaned, None
