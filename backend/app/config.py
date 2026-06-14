from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Voice Draw"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 语音识别（OpenAI Whisper API）
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    speech_model: str = "whisper-1"
    speech_language: str | None = "zh"
    speech_timeout_seconds: float = 60.0

    # 图像生成（auto=有 Key 用 OpenAI，否则 Pollinations 免费服务）
    image_provider: str = "auto"
    image_api_key: str | None = None
    image_model: str = "dall-e-3"
    image_quality: str = "standard"
    image_timeout_seconds: float = 120.0
    pollinations_base_url: str = "https://image.pollinations.ai"
    pollinations_model: str | None = None

    # Stable Horde 免费图像生成（无需注册，匿名 Key）
    stable_horde_api_key: str = "0000000000"
    stable_horde_base_url: str = "https://stablehorde.net/api/v2"
    stable_horde_steps: int = 20
    stable_horde_poll_interval: float = 3.0
    stable_horde_max_wait_seconds: float = 180.0
    stable_horde_models: str = ""

    # 提示词优化
    prompt_optimizer_use_openai: bool = True
    prompt_optimizer_fallback_rules: bool = True
    prompt_optimizer_model: str = "gpt-4o-mini"
    prompt_optimizer_timeout_seconds: float = 30.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_image_api_key(self) -> str | None:
        return self.image_api_key or self.openai_api_key

    @property
    def stable_horde_models_list(self) -> list[str]:
        if not self.stable_horde_models.strip():
            return []
        return [model.strip() for model in self.stable_horde_models.split(",") if model.strip()]


settings = Settings()
