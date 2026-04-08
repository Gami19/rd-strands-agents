"""フェーズ3: API 経路のガード（カタログ・一覧・workflow 403）。DATA_ROOT はテストごとに分離する。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infrastructure.project_meta import META_FILENAME
from src.infrastructure.workspace import ensure_project_workspace, project_workspace


@pytest.fixture
def client(monkeypatch, tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    import src.api.projects_api as projects_api
    import src.infrastructure.workspace as ws

    monkeypatch.setattr(ws, "DATA_ROOT", root)
    monkeypatch.setattr(projects_api, "DATA_ROOT", root)
    from fastapi.testclient import TestClient

    from src.api.main import app

    return TestClient(app)


def _write_meta(project_id: str, data: dict) -> None:
    ensure_project_workspace(project_id)
    p = project_workspace(project_id) / META_FILENAME
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_catalog_resolves_marketing_team_context(client) -> None:
    _write_meta("p-mkt", {"display_name": "M", "team_context": "marketing"})
    r = client.get("/api/skills/catalog", params={"project_id": "p-mkt"})
    assert r.status_code == 200
    body = r.json()
    assert body["team_context"] == "marketing"
    assert Path(body["skills_root"]).name == "pr"


def test_catalog_corrupt_meta_422(client) -> None:
    ensure_project_workspace("p-bad")
    bad = project_workspace("p-bad") / META_FILENAME
    bad.write_text("{not json", encoding="utf-8")
    r = client.get("/api/skills/catalog", params={"project_id": "p-bad"})
    assert r.status_code == 422
    d = r.json()["detail"]
    assert isinstance(d, dict)
    assert "message" in d


def test_list_projects_includes_meta_error_for_corrupt_json(client) -> None:
    ensure_project_workspace("p-bad2")
    bad = project_workspace("p-bad2") / META_FILENAME
    bad.write_text("{x", encoding="utf-8")
    r = client.get("/api/projects")
    assert r.status_code == 200
    items = r.json()["items"]
    row = next(x for x in items if x["project_id"] == "p-bad2")
    assert row.get("meta_error") is True
    assert isinstance(row.get("detail"), str) and row["detail"]


def test_workflow_chat_403_for_non_developer(client) -> None:
    _write_meta("p-tm", {"display_name": "T", "team_context": "marketing"})
    r = client.post(
        "/api/chat",
        json={
            "message": "hi",
            "mode": "workflow",
            "project_id": "p-tm",
            "agent_id": "convert-pdf",
        },
    )
    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["code"] == "workflow_requires_developer"
    assert "message" in detail
