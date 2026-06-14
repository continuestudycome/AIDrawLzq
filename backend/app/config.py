from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Voice Draw"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 语音识别（local=本地 Whisper 免费 / openai=Whisper API）
    speech_provider: str = "local"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    speech_model: str = "whisper-1"
    speech_language: str | None = "zh"
    speech_timeout_seconds: float = 60.0
    whisper_local_model: str = "base"
    whisper_local_language: str = "zh"
    whisper_local_device: str = "cpu"
    whisper_local_compute_type: str = "int8"
    whisper_local_model_path: str | None = None
    huggingface_endpoint: str = "https://hf-mirror.com"
    huggingface_hub_disable_ssl: bool = True

    # 图像生成（stablehorde=Stable Horde 免费 / openai=OpenAI / auto=有 Key 用 OpenAI 否则 Stable Horde）
    image_provider: str = "stablehorde"
    image_api_key: str | None = None
    image_model: str = "dall-e-3"
    image_quality: str = "standard"
    image_timeout_seconds: float = 120.0
    pollinations_base_url: str = "https://image.pollinations.ai"
    pollinations_model: str | None = None

    # Stable Horde 免费图像生成（无需注册，匿名 Key）
    stable_horde_api_key: str = "0000000000"
    stable_horde_base_url: str = "https://stablehorde.net/api/v2"
    stable_horde_steps: int = 28
    stable_horde_poll_interval: float = 3.0
    stable_horde_max_wait_seconds: float = 180.0
    stable_horde_models: str = "Deliberate"
    stable_horde_negative_prompt: str = (
        "low quality, blurry, distorted, deformed, ugly, bad anatomy, bad hands, "
        "extra limbs, text, watermark, logo, signature, cropped, worst quality"
    )

    # 提示词优化（ollama=本地 Ollama / openai=OpenAI / rules=规则）
    prompt_optimizer_provider: str = "ollama"
    prompt_optimizer_fallback_rules: bool = True
    prompt_optimizer_model: str = "gpt-4o-mini"
    prompt_optimizer_timeout_seconds: float = 30.0
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 120.0
    ollama_temperature: float = 0.5
    ollama_num_predict: int = 256
    ollama_num_ctx: int = 2048
    ollama_keep_alive: str = "30m"
    ollama_warmup_on_startup: bool = True
    ollama_cache_enabled: bool = True
    ollama_cache_max_items: int = 128

    # 生成历史
    history_enabled: bool = True
    history_dir: str | None = None
    history_max_items: int = 100

    @property
    def backend_dir(self) -> Path:
        return _BACKEND_DIR

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

from app.hub_environment import configure_huggingface_hub

configure_huggingface_hub(settings)
