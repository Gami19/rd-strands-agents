"""project_id から team_context・skills_root を解決する。"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.infrastructure.project_meta import read_team_context
from src.infrastructure.team_context import (
    resolve_skills_root,
    TEAM_CONTEXT_DEVELOPER,
)
from src.infrastructure.workspace import ensure_project_workspace

logger = logging.getLogger(__name__)

_DEBUG_ENV = "STRANDS_DEBUG_PROJECT_CONTEXT"


def _debug_project_context_enabled() -> bool:
    v = os.environ.get(_DEBUG_ENV, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def log_project_skills_resolution(
    project_id: str,
    team_context: str,
    skills_root: Path,
) -> None:
    if _debug_project_context_enabled():
        logger.debug(
            "project_context project_id=%s team_context=%s skills_root=%s",
            project_id,
            team_context,
            skills_root.resolve(),
        )


def resolve_skills_for_project(project_id: str) -> tuple[str, Path]:
    ws = ensure_project_workspace(project_id)
    tc = read_team_context(ws)
    root = resolve_skills_root(tc)
    log_project_skills_resolution(project_id, tc, root)
    return tc, root


def get_team_context_for_project(project_id: str) -> str:
    tc, _root = resolve_skills_for_project(project_id)
    return tc


def get_skills_root_for_project(project_id: str) -> Path:
    _tc, root = resolve_skills_for_project(project_id)
    return root


def get_skills_root_for_developer_default() -> Path:
    """project_id 省略時のカタログ用（developer 相当）。"""
    root = resolve_skills_root(TEAM_CONTEXT_DEVELOPER)
    log_project_skills_resolution("(catalog_fallback)", TEAM_CONTEXT_DEVELOPER, root)
    return root
