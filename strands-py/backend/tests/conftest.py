import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))


def pytest_configure(config) -> None:
    """pytest 実行中は起動シードを無効化し、開発者 data への書き込みを避ける。"""
    import os

    os.environ["STRANDS_SKIP_SEED_PROJECTS"] = "1"
