"""Team 文脈に応じたエージェント YAML を Workspace の agents/ へ冪等コピーする。

コピー元はリポジトリ内 `backend/agent/seed_projects/team-<team_context>/agents/`（起動時シードと同一）。
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from src.infrastructure.agent_definitions import agents_dir
from src.infrastructure.team_context import TEAM_CONTEXT_DEVELOPER, VALID_TEAM_CONTEXTS
from src.infrastructure.workspace import STRANDS_PY_ROOT

logger = logging.getLogger(__name__)

_SEED_PROJECTS_ROOT = STRANDS_PY_ROOT / "backend" / "agent" / "seed_projects"


def seed_projects_agents_root() -> Path:
    return _SEED_PROJECTS_ROOT.resolve()


def seed_team_agents_if_needed(workspace_root: Path, team_context: str) -> None:
    """
    team_context が developer 以外のとき、seed_projects/team-<tc>/agents/ 内の *.yaml / *.yml を
    workspace の agents/ にコピーする。同名ファイルが既にあれば上書きしない。
    """
    tc = (team_context or "").strip().lower()
    if tc == TEAM_CONTEXT_DEVELOPER or tc not in VALID_TEAM_CONTEXTS:
        return

    src_dir = (_SEED_PROJECTS_ROOT / f"team-{tc}" / "agents").resolve()
    if not src_dir.is_dir():
        logger.debug("シード agents ディレクトリがありません: %s", src_dir)
        return

    ws = workspace_root.resolve()
    dest_dir = agents_dir(ws)
    dest_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(src_dir.glob("*.yaml")) + sorted(src_dir.glob("*.yml"))
    for src in sources:
        if not src.is_file():
            continue
        dest = dest_dir / src.name
        if dest.is_file():
            continue
        try:
            shutil.copy2(src, dest)
            logger.info(
                "エージェント YAML をコピーしました: %s -> %s",
                src.name,
                dest,
            )
        except OSError as e:
            logger.warning("エージェント YAML のコピーに失敗: %s -> %s (%s)", src, dest, e)
