from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.draw import (
    DrawRequest,
    DrawResponse,
    OptimizePromptRequest,
    OptimizePromptResponse,
    SpeechToTextResponse,
    TranscriptRequest,
)
from app.services.image_generation import (
    ImageGenerationError,
    ImageGenerationNotConfiguredError,
    generate_image as create_image_from_prompt,
)
from app.services.prompt_optimizer import PromptOptimizerError, optimize_prompt
from app.services.speech_recognition import (
    SpeechRecognitionError,
    SpeechRecognitionNotConfiguredError,
    transcribe_audio,
)

router = APIRouter(prefix="/api", tags=["draw"])


async def _build_draw_response(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> DrawResponse:
    try:
        image_url, message = await create_image_from_prompt(prompt, width=width, height=height)
    except ImageGenerationNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ImageGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DrawResponse(
        prompt=prompt,
        image_url=image_url,
        message=message,
    )


@router.post("/optimize-prompt", response_model=OptimizePromptResponse)
async def optimize_prompt_endpoint(payload: OptimizePromptRequest) -> OptimizePromptResponse:
    """优化提示词，扩展为更适合 AI 绘图的描述。"""
    try:
        optimized, message, method = await optimize_prompt(payload.text)
    except PromptOptimizerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return OptimizePromptResponse(
        original=payload.text.strip(),
        optimized=optimized,
        message=message,
        method=method,
    )


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio: UploadFile = File(...)) -> SpeechToTextResponse:
    """接收语音文件，通过 Whisper API 返回识别文本。"""
    audio_bytes = await audio.read()

    try:
        text, confidence = await transcribe_audio(
            audio_bytes,
            filename=audio.filename or "recording.webm",
            content_type=audio.content_type,
        )
    except SpeechRecognitionNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SpeechRecognitionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SpeechToTextResponse(text=text, confidence=confidence)


@router.post("/transcript", response_model=DrawResponse)
async def draw_from_transcript(payload: TranscriptRequest) -> DrawResponse:
    """根据文本生成图像。"""
    return await _build_draw_response(payload.text)


@router.post("/generate", response_model=DrawResponse)
async def generate_image(payload: DrawRequest) -> DrawResponse:
    """根据提示词生成图像。"""
    return await _build_draw_response(
        payload.prompt,
        width=payload.width,
        height=payload.height,
    )
