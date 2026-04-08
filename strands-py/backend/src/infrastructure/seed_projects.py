"""起動時にチーム文脈ごとのサンプルプロジェクトを未作成なら用意する。"""

from __future__ import annotations

import logging
import os

from src.infrastructure.project_meta import write_project_meta
from src.infrastructure.team_agent_defaults import seed_team_agents_if_needed
from src.infrastructure.team_context import TEAM_CONTEXT_DEVELOPER, team_context_labels
from src.infrastructure.workspace import ensure_project_workspace, project_workspace

logger = logging.getLogger(__name__)

_SKIP_SEED_ENV = "STRANDS_SKIP_SEED_PROJECTS"


def _skip_seed_projects() -> bool:
    v = os.environ.get(_SKIP_SEED_ENV, "").strip().lower()
    return v in ("1", "true", "yes", "on")


# project_id は projects_api の検証に合わせる。表示名は team_context_labels と対応。
SEED_TEAM_PROJECTS: tuple[tuple[str, str], ...] = (
    ("team-developer", TEAM_CONTEXT_DEVELOPER),
    ("team-marketing", "marketing"),
    ("team-hr", "hr"),
    ("team-pmo", "pmo"),
    ("team-engineering", "engineering"),
)


def ensure_seed_team_projects() -> None:
    """各 team_context 用 workspace を用意し、未作成ならメタを書く。agents は seed_projects から冪等コピー。"""
    if _skip_seed_projects():
        return
    for project_id, tc in SEED_TEAM_PROJECTS:
        path = project_workspace(project_id)
        newly_created = not path.exists()
        if newly_created:
            ensure_project_workspace(project_id)
            display_name = team_context_labels[tc]
            write_project_meta(path, display_name=display_name, team_context=tc)
            logger.info(
                "seed project created: project_id=%s team_context=%s display_name=%s",
                project_id,
                tc,
                display_name,
            )
        else:
            ensure_project_workspace(project_id)
        seed_team_agents_if_needed(path, tc)
