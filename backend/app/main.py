import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import draw, health, history

logger = logging.getLogger(__name__)


def _should_warmup_ollama() -> bool:
    if not settings.ollama_warmup_on_startup:
        return False
    provider = settings.prompt_optimizer_provider.lower().strip()
    if provider == "ollama":
        return True
    return provider == "auto" and not settings.dashscope_api_key


def _warn_dashscope_key_override() -> None:
    if not settings.dashscope_key_conflict_resolved:
        return

    logger.warning(
        "检测到 DASHSCOPE_API_KEY 冲突：系统环境变量与 backend/.env 不一致，"
        "已优先使用 .env 中的 Key。建议删除 Windows 用户环境变量 DASHSCOPE_API_KEY 以免混淆。"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _warn_dashscope_key_override()

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
