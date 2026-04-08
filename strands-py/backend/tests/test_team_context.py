from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infrastructure.project_meta import (
    META_FILENAME,
    ProjectMetaJsonError,
    read_meta_dict,
    read_team_context,
    write_display_name,
    write_project_meta,
)
from src.infrastructure.team_context import (
    normalize_team_context,
    resolve_skills_root,
    resolve_workflows_root,
    workflow_enabled,
)


def test_normalize_team_context() -> None:
    assert normalize_team_context(None) == "developer"
    assert normalize_team_context("") == "developer"
    assert normalize_team_context("DEVELOPER") == "developer"
    assert normalize_team_context("marketing") == "marketing"
    assert normalize_team_context("unknown") == "developer"


def test_resolve_skills_root_paths() -> None:
    dev = resolve_skills_root("developer")
    pr = resolve_skills_root("marketing")
    assert dev.name == "dev"
    assert pr.name == "pr"
    assert dev.parent == pr.parent


def test_workflow_enabled() -> None:
    assert workflow_enabled("developer") is True
    assert workflow_enabled("marketing") is False


def test_resolve_workflows_root_name() -> None:
    assert resolve_workflows_root().name == "dev"


def test_read_meta_dict_missing(tmp_path: Path) -> None:
    assert read_meta_dict(tmp_path) == {}


def test_read_meta_dict_corrupt(tmp_path: Path) -> None:
    p = tmp_path / META_FILENAME
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ProjectMetaJsonError):
        read_meta_dict(tmp_path)


def test_write_display_name_preserves_team_context(tmp_path: Path) -> None:
    write_project_meta(tmp_path, display_name="A", team_context="marketing")
    write_display_name(tmp_path, "B")
    data = read_meta_dict(tmp_path)
    assert data["display_name"] == "B"
    assert data["team_context"] == "marketing"


def test_read_team_context_default(tmp_path: Path) -> None:
    (tmp_path / META_FILENAME).write_text(
        json.dumps({"display_name": "X"}, ensure_ascii=False),
        encoding="utf-8",
    )
    assert read_team_context(tmp_path) == "developer"
