from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.infrastructure.project_meta import ProjectMetaJsonError
from src.infrastructure.project_runtime import (
    get_skills_root_for_developer_default,
    resolve_skills_for_project,
)
from src.infrastructure.skill_policy import list_skill_catalog
from src.infrastructure.workspace import ensure_project_workspace

router = APIRouter(tags=["skills"])

_PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def _validate_project_id_optional(project_id: str | None) -> None:
    if project_id is None:
        return
    if not project_id or len(project_id) > 128 or not _PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=422, detail="無効な project_id です")


@router.get("/skills/catalog")
async def skills_catalog(
    project_id: str | None = Query(
        default=None,
        description="省略時は developer 相当の skills ルート（移行互換）",
    ),
) -> dict[str, Any]:
    _validate_project_id_optional(project_id)
    if project_id is None:
        skills_root = get_skills_root_for_developer_default()
        tc = "developer"
    else:
        try:
            ensure_project_workspace(project_id)
            tc, skills_root = resolve_skills_for_project(project_id)
        except ProjectMetaJsonError as e:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": str(e),
                    "hint": ".strands-project.json を修正するか、プロジェクトフォルダ内から削除してください。",
                },
            ) from e
    exists = skills_root.is_dir()
    items = list_skill_catalog(skills_root) if exists else []
    return {
        "project_id": project_id,
        "team_context": tc,
        "skills_root": str(skills_root.resolve()) if exists else str(skills_root),
        "skills_root_exists": exists,
        "items": items,
    }
