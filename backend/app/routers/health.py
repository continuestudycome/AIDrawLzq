import httpx
from fastapi import APIRouter

from app.config import settings
from app.services.image_generation import (
    ImageGenerationNotConfiguredError,
    resolve_image_provider,
)
from app.services.speech_recognition import resolve_speech_provider

router = APIRouter(tags=["health"])


async def _check_ollama_available() -> bool | None:
    provider = settings.prompt_optimizer_provider.lower().strip()
    if provider not in {"ollama", "auto"}:
        return None

    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@router.get("/health")
async def health_check() -> dict[str, str | bool | None]:
    try:
        image_provider = resolve_image_provider()
    except ImageGenerationNotConfiguredError:
        image_provider = "misconfigured"

    return {
        "status": "ok",
        "speech_provider": resolve_speech_provider(),
        "image_provider": image_provider,
        "prompt_optimizer": settings.prompt_optimizer_provider,
        "history_enabled": settings.history_enabled,
        "ollama_available": await _check_ollama_available(),
    }
