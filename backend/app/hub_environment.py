"""Hugging Face Hub 环境配置：镜像、证书与 SSL（须在 hub 下载前执行）。"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings

_configured = False


def configure_huggingface_hub(settings: Settings) -> None:
    """配置 HF 镜像与 SSL，避免 Whisper 模型下载失败。"""
    global _configured
    if _configured:
        return

    if settings.huggingface_endpoint:
        os.environ["HF_ENDPOINT"] = settings.huggingface_endpoint.rstrip("/")

    try:
        import certifi

        cert_path = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", cert_path)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)
    except ImportError:
        pass

    if settings.huggingface_hub_disable_ssl:
        _patch_hub_ssl_verification_disabled()

    _configured = True


def _patch_hub_ssl_verification_disabled() -> None:
    """用户显式开启 HUGGINGFACE_HUB_DISABLE_SSL 时，跳过 HTTPS 证书校验。"""
    try:
        import httpx
        from huggingface_hub.utils._http import close_session, set_client_factory
    except ImportError:
        return

    def client_factory() -> httpx.Client:
        return httpx.Client(
            verify=False,
            follow_redirects=True,
            timeout=None,
        )

    set_client_factory(client_factory)
    close_session()
