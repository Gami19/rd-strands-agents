from __future__ import annotations

from pathlib import Path


STRANDS_PY_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = STRANDS_PY_ROOT / "data"

# Skills / Workflows の解決は team_context / project_runtime を使用すること。
# 後方参照用（レガシー・スクリプト向け）:
WORKFLOWS_ROOT = STRANDS_PY_ROOT / "backend" / "agent" / "workflows" / "dev"

PROJECT_SUBDIRS = ("inbox", "notes", "proposal", "decision")

# 成果物一覧・ファイル配信で agents を含める（単一レイヤのファイルのみ）。
ARTIFACT_LIST_SUBDIRS = (*PROJECT_SUBDIRS, "agents")


def project_workspace(project_id: str) -> Path:
    return DATA_ROOT / "projects" / project_id


def ensure_project_workspace(project_id: str) -> Path:
    base = project_workspace(project_id)
    for name in PROJECT_SUBDIRS:
        (base / name).mkdir(parents=True, exist_ok=True)
    (base / "agents").mkdir(parents=True, exist_ok=True)
    return base

