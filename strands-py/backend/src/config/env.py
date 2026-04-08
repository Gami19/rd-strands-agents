from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_app_env() -> None:
    """
    backend/.env（このリポジトリでは strands-py/backend/.env）を読み込む。

    この関数は `backend/main.py` ではなく `backend/src/*` 側から呼ぶ前提。
    """

    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)

