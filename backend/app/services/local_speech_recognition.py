"""本地 Whisper 语音识别：免费离线，无需 API Key。"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from app.config import settings

_model = None
_model_lock = asyncio.Lock()


class LocalSpeechRecognitionError(Exception):
    """本地语音识别失败。"""


def _resolve_model_source() -> str:
    if settings.whisper_local_model_path:
        model_path = Path(settings.whisper_local_model_path).expanduser()
        if not model_path.exists():
            raise LocalSpeechRecognitionError(
                f"本地模型路径不存在: {model_path}。请检查 WHISPER_LOCAL_MODEL_PATH"
            )
        return str(model_path)

    default_local = Path(__file__).resolve().parents[2] / "models" / f"faster-whisper-{settings.whisper_local_model}"
    if default_local.exists():
        return str(default_local)

    return settings.whisper_local_model


def _load_model():
    global _model
    if _model is not None:
        return _model

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise LocalSpeechRecognitionError(
            "未安装 faster-whisper，请运行: pip install faster-whisper"
        ) from exc

    model_source = _resolve_model_source()

    try:
        _model = WhisperModel(
            model_source,
            device=settings.whisper_local_device,
            compute_type=settings.whisper_local_compute_type,
        )
    except Exception as exc:
        hint = (
            "若下载模型失败，请运行: python scripts/download_whisper_model.py "
            "或在 .env 设置 HUGGINGFACE_ENDPOINT=https://hf-mirror.com 后重启"
        )
        raise LocalSpeechRecognitionError(f"加载 Whisper 模型失败: {exc}。{hint}") from exc

    return _model


def _transcribe_file(audio_path: str) -> str:
    model = _load_model()
    language = settings.whisper_local_language or "zh"
    segments, _ = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )
    return "".join(segment.text for segment in segments).strip()


async def transcribe_local_audio(
    audio_bytes: bytes,
    *,
    filename: str = "recording.webm",
) -> tuple[str, float | None]:
    """使用本地 Whisper 模型识别音频。"""
    if not audio_bytes:
        raise LocalSpeechRecognitionError("音频内容为空")

    suffix = Path(filename).suffix or ".webm"
    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        async with _model_lock:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, _transcribe_file, temp_path)
    except LocalSpeechRecognitionError:
        raise
    except Exception as exc:
        raise LocalSpeechRecognitionError(f"本地语音识别失败: {exc}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

    if not text:
        raise LocalSpeechRecognitionError("语音识别结果为空，请重新录音")

    return text, None
