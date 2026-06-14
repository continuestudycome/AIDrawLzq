from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    id: str
    created_at: str
    display_prompt: str = Field(description="中文展示提示词")
    generation_prompt: str = Field(description="实际用于绘图的提示词")
    image_url: str
    message: str = ""
    width: int = 512
    height: int = 512


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
