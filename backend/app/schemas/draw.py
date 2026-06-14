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


class OptimizePromptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="待优化的提示词")


class OptimizePromptResponse(BaseModel):
    original: str
    optimized: str = Field(description="中文展示版，显示在输入框供用户阅读")
    optimized_en: str = Field(description="英文绘图版，生成图像时使用")
    message: str
    method: str = "rules"
