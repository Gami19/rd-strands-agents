from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.infrastructure.agent_definitions import list_agent_definitions
from src.infrastructure.workspace import ensure_project_workspace

router = APIRouter(tags=["agents"])

PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def _validate_project_id(project_id: str) -> None:
    if not project_id or len(project_id) > 128 or not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=422, detail="無効な project_id です")


@router.get("/agents")
async def list_agents(
    project_id: str = Query(
        ...,
        description=(
            "projects/<project_id>/agents の YAML を列挙。kind=orchestrator は "
            "POST /api/chat の mode=orchestrate 用。現行 Web UI のチャットでは未使用。"
        ),
    ),
) -> dict[str, Any]:
    _validate_project_id(project_id)
    ws = ensure_project_workspace(project_id)
    items = []
    for m in list_agent_definitions(ws):
        if m.kind == "orchestrator":
            continue
        items.append(
            {
                "agent_id": m.agent_id,
                "name": m.name,
                "kind": m.kind,
                "description": m.description,
                "department": m.department or None,
                "division": m.division or None,
                "icon_key": m.icon_key or None,
            }
        )
    return {"project_id": project_id, "items": items}

