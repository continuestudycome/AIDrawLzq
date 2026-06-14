r"""预下载 faster-whisper 模型到本地，避免首次语音识别时在线下载失败。

用法（在 backend 目录）:
    .\.venv\Scripts\python.exe scripts\download_whisper_model.py
    .\.venv\Scripts\python.exe scripts\download_whisper_model.py --model tiny
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import settings  # noqa: E402  触发 hub 环境配置
from huggingface_hub import snapshot_download


MODEL_REPO = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 faster-whisper 模型到 backend/models/")
    parser.add_argument(
        "--model",
        default=settings.whisper_local_model,
        choices=list(MODEL_REPO.keys()),
        help="模型大小，默认读取 WHISPER_LOCAL_MODEL",
    )
    args = parser.parse_args()

    repo_id = MODEL_REPO[args.model]
    local_dir = _BACKEND_DIR / "models" / f"faster-whisper-{args.model}"

    print(f"下载 {repo_id} -> {local_dir}")
    print(f"镜像: {settings.huggingface_endpoint}")

    path = snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
    )

    print("\n下载完成!")
    print(f"模型目录: {path}")
    print("\n请在 backend/.env 中添加:")
    print(f"WHISPER_LOCAL_MODEL_PATH={local_dir}")
    print("然后重启后端。")


if __name__ == "__main__":
    main()
