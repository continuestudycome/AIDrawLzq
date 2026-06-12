from fastapi import APIRouter, File, UploadFile

from app.schemas.draw import DrawRequest, DrawResponse, SpeechToTextResponse, TranscriptRequest
from app.services.placeholder_image import build_placeholder_image_data_url

router = APIRouter(prefix="/api", tags=["draw"])


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio: UploadFile = File(...)) -> SpeechToTextResponse:
    """接收语音文件，返回识别文本（当前为占位实现）。"""
    _ = await audio.read()
    return SpeechToTextResponse(
        text="一只在星空下奔跑的猫",
        confidence=0.95,
    )


@router.post("/transcript", response_model=DrawResponse)
async def draw_from_transcript(payload: TranscriptRequest) -> DrawResponse:
    """根据文本生成图像（当前为占位实现）。"""
    return DrawResponse(
        prompt=payload.text,
        image_url=build_placeholder_image_data_url(payload.text),
        message="占位预览图已生成（真实 AI 绘图尚未接入）",
    )


@router.post("/generate", response_model=DrawResponse)
async def generate_image(payload: DrawRequest) -> DrawResponse:
    """根据提示词生成图像（当前为占位实现）。"""
    return DrawResponse(
        prompt=payload.prompt,
        image_url=build_placeholder_image_data_url(
            payload.prompt,
            width=payload.width,
            height=payload.height,
        ),
        message="占位预览图已生成（真实 AI 绘图尚未接入）",
    )
