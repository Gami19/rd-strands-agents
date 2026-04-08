"""team_context と Skills / Workflows ルートのテーブル駆動解決。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.infrastructure.workspace import STRANDS_PY_ROOT

logger = logging.getLogger(__name__)

TEAM_CONTEXT_DEVELOPER = "developer"
VALID_TEAM_CONTEXTS: frozenset[str] = frozenset(
    {
        TEAM_CONTEXT_DEVELOPER,
        "marketing",
        "hr",
        "pmo",
        "engineering",
    }
)

team_context_labels: dict[str, str] = {
    TEAM_CONTEXT_DEVELOPER: "Developer",
    "marketing": "Marketing Teams",
    "hr": "HR Teams",
    "pmo": "PMO Teams",
    "engineering": "Engineering Teams",
}


def normalize_team_context(raw: Any) -> str:
    if raw is None:
        return TEAM_CONTEXT_DEVELOPER
    if not isinstance(raw, str):
        logger.warning("team_context が文字列ではありません: %r → developer に正規化", raw)
        return TEAM_CONTEXT_DEVELOPER
    s = raw.strip().lower()
    if not s or s not in VALID_TEAM_CONTEXTS:
        if s:
            logger.warning("未知の team_context %r → developer に正規化", raw)
        return TEAM_CONTEXT_DEVELOPER
    return s


def resolve_skills_root(team_context: str) -> Path:
    base = STRANDS_PY_ROOT / "backend" / "agent" / "skills"
    if team_context == TEAM_CONTEXT_DEVELOPER:
        return base / "dev"
    return base / "pr"


def resolve_workflows_root() -> Path:
    return STRANDS_PY_ROOT / "backend" / "agent" / "workflows" / "dev"


def workflow_enabled(team_context: str) -> bool:
    return team_context == TEAM_CONTEXT_DEVELOPER
