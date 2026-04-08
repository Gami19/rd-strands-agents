"""プロジェクト workspace の一覧・作成・削除・更新。"""

from __future__ import annotations

import re
import shutil
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.infrastructure.project_meta import (
    ProjectMetaJsonError,
    read_meta_dict,
    write_project_meta,
)
from src.infrastructure.team_context import (
    normalize_team_context,
    team_context_labels,
    VALID_TEAM_CONTEXTS,
)
from src.infrastructure.team_agent_defaults import seed_team_agents_if_needed
from src.infrastructure.workspace import DATA_ROOT, ensure_project_workspace, project_workspace

router = APIRouter(tags=["projects"])

PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def _validate_project_id(project_id: str) -> None:
    if not project_id or len(project_id) > 128 or not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=422, detail="無効な project_id です")


@router.get("/projects")
async def list_projects() -> dict[str, Any]:
    root = DATA_ROOT / "projects"
    if not root.is_dir():
        return {"items": []}
    names = sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )
    items: list[dict[str, Any]] = []
    for n in names:
        ws = project_workspace(n)
        try:
            data = read_meta_dict(ws)
        except ProjectMetaJsonError as e:
            items.append(
                {
                    "project_id": n,
                    "display_name": n,
                    "meta_error": True,
                    "detail": str(e),
                }
            )
            continue
        dn_raw = data.get("display_name")
        if isinstance(dn_raw, str) and dn_raw.strip():
            display_name = dn_raw.strip()
        else:
            display_name = n
        tc = normalize_team_context(data.get("team_context"))
        items.append(
            {
                "project_id": n,
                "display_name": display_name,
                "team_context": tc,
                "team_context_label": team_context_labels.get(tc, tc),
            }
        )
    return {"items": items}


def _validate_team_context_field(v: object) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise TypeError("team_context は文字列にしてください")
    s = v.strip().lower()
    if not s:
        return None
    if s not in VALID_TEAM_CONTEXTS:
        raise ValueError(
            f"無効な team_context です。次のいずれか: {', '.join(sorted(VALID_TEAM_CONTEXTS))}"
        )
    return s


class CreateProjectBody(BaseModel):
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    display_name: str | None = Field(
        default=None,
        max_length=200,
        description="表示名（日本語可）。省略時は project_id と同じ。",
    )
    team_context: str | None = Field(
        default=None,
        description="developer / marketing / hr / pmo / engineering。省略時は developer。",
    )

    @field_validator("display_name", mode="before")
    @classmethod
    def _normalize_display_name(cls, v: object) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise TypeError("display_name は文字列にしてください")
        s = v.strip()
        if not s:
            return None
        if any(ord(c) < 32 for c in s):
            raise ValueError("表示名に制御文字は使えません")
        return s

    @field_validator("team_context", mode="before")
    @classmethod
    def _v_team_context(cls, v: object) -> str | None:
        return _validate_team_context_field(v)


@router.post("/projects")
async def create_project(body: CreateProjectBody) -> dict[str, Any]:
    _validate_project_id(body.project_id)
    path = project_workspace(body.project_id)
    created = not path.exists()
    ensure_project_workspace(body.project_id)
    effective_name = body.display_name if body.display_name else body.project_id
    tc_norm = normalize_team_context(body.team_context)

    if created:
        write_project_meta(path, display_name=effective_name, team_context=tc_norm)
    else:
        if body.display_name is not None or body.team_context is not None:
            try:
                data = read_meta_dict(path)
            except ProjectMetaJsonError as e:
                raise HTTPException(
                    status_code=422,
                    detail=str(e),
                ) from e
            cur_dn = data.get("display_name")
            cur_name = (
                cur_dn.strip()
                if isinstance(cur_dn, str) and cur_dn.strip()
                else body.project_id
            )
            cur_tc = normalize_team_context(data.get("team_context"))
            new_dn = effective_name if body.display_name is not None else cur_name
            new_tc = tc_norm if body.team_context is not None else cur_tc
            write_project_meta(path, display_name=new_dn, team_context=new_tc)
            effective_name = new_dn
            tc_norm = new_tc
        else:
            try:
                data = read_meta_dict(path)
            except ProjectMetaJsonError as e:
                raise HTTPException(status_code=422, detail=str(e)) from e
            dn_raw = data.get("display_name")
            if isinstance(dn_raw, str) and dn_raw.strip():
                effective_name = dn_raw.strip()
            tc_norm = normalize_team_context(data.get("team_context"))

    seed_team_agents_if_needed(path, tc_norm)

    return {
        "project_id": body.project_id,
        "display_name": effective_name,
        "team_context": tc_norm,
        "team_context_label": team_context_labels.get(tc_norm, tc_norm),
        "created": created,
    }


class PatchProjectBody(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    team_context: str | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def _normalize_display_name_patch(cls, v: object) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise TypeError("display_name は文字列にしてください")
        s = v.strip()
        if not s:
            return None
        if any(ord(c) < 32 for c in s):
            raise ValueError("表示名に制御文字は使えません")
        return s

    @field_validator("team_context", mode="before")
    @classmethod
    def _v_team_context_patch(cls, v: object) -> str | None:
        return _validate_team_context_field(v)


@router.patch("/projects/{project_id}")
async def patch_project(project_id: str, body: PatchProjectBody) -> dict[str, Any]:
    _validate_project_id(project_id)
    path = project_workspace(project_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    if body.display_name is None and body.team_context is None:
        raise HTTPException(
            status_code=422,
            detail="display_name または team_context のいずれかを指定してください",
        )
    try:
        data = read_meta_dict(path)
    except ProjectMetaJsonError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    dn_raw = data.get("display_name")
    cur_name = (
        dn_raw.strip()
        if isinstance(dn_raw, str) and dn_raw.strip()
        else project_id
    )
    cur_tc = normalize_team_context(data.get("team_context"))
    new_dn = body.display_name if body.display_name is not None else cur_name
    new_tc = (
        normalize_team_context(body.team_context)
        if body.team_context is not None
        else cur_tc
    )
    write_project_meta(path, display_name=new_dn, team_context=new_tc)
    ensure_project_workspace(project_id)
    seed_team_agents_if_needed(path, new_tc)
    return {
        "project_id": project_id,
        "display_name": new_dn,
        "team_context": new_tc,
        "team_context_label": team_context_labels.get(new_tc, new_tc),
    }


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str) -> dict[str, Any]:
    _validate_project_id(project_id)
    if project_id == "default":
        raise HTTPException(status_code=403, detail="default プロジェクトは削除できません")
    path = project_workspace(project_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    shutil.rmtree(path)
    return {"project_id": project_id, "deleted": True}
