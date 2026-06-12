from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="语音识别后的文本")


class SpeechToTextResponse(BaseModel):
    text: str
    confidence: float | None = None


class DrawRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="绘图提示词")
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)


class DrawResponse(BaseModel):
    prompt: str
    image_url: str | None = None
    message: str = "ok"
