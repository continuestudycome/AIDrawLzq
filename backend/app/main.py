from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import draw, health, history


def _should_warmup_ollama() -> bool:
    if not settings.ollama_warmup_on_startup:
        return False
    provider = settings.prompt_optimizer_provider.lower().strip()
    if provider == "ollama":
        return True
    return provider == "auto" and not settings.dashscope_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _should_warmup_ollama():
        try:
            from app.services.ollama_client import warmup_ollama_model

            await warmup_ollama_model()
        except Exception:
            pass

    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(draw.router)
app.include_router(history.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} API", "docs": "/docs"}
