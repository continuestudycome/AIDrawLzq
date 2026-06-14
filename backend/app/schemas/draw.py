from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="用于绘图的提示词")
    display_prompt: str | None = Field(
        default=None,
        max_length=2000,
        description="中文展示提示词，用于历史记录展示",
    )


class SpeechToTextResponse(BaseModel):
    text: str
    confidence: float | None = None


class DrawRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="绘图提示词")
    display_prompt: str | None = Field(
        default=None,
        max_length=2000,
        description="中文展示提示词，用于历史记录展示",
    )
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)


class DrawResponse(BaseModel):
    prompt: str
    image_url: str | None = None
    message: str = "ok"
    history_id: str | None = None


class OptimizePromptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="待优化的提示词")


class OptimizePromptResponse(BaseModel):
    original: str
    optimized: str = Field(description="中文展示版，显示在输入框供用户阅读")
    optimized_en: str = Field(description="英文绘图版，生成图像时使用")
    message: str
    method: str = "rules"
