"""フェーズ4: Team プロジェクト作成時の既定エージェントシードと agents API 拡張。"""

from __future__ import annotations

import pytest

from src.infrastructure.seed_projects import ensure_seed_team_projects
from src.infrastructure.workspace import project_workspace


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


def test_post_projects_marketing_seeds_default_agent(client) -> None:
    r = client.post(
        "/api/projects",
        json={
            "project_id": "p4-mkt",
            "display_name": "Phase4 M",
            "team_context": "marketing",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["created"] is True
    assert body["team_context"] == "marketing"
    yaml_path = project_workspace("p4-mkt") / "agents" / "marketing-copy.yaml"
    assert yaml_path.is_file()
    yaml_path2 = project_workspace("p4-mkt") / "agents" / "review.yaml"
    assert yaml_path2.is_file()


def test_post_projects_marketing_seed_idempotent(client) -> None:
    body = {
        "project_id": "p4-idem",
        "display_name": "Idem",
        "team_context": "marketing",
    }
    r1 = client.post("/api/projects", json=body)
    assert r1.status_code == 200
    p = project_workspace("p4-idem") / "agents" / "marketing-copy.yaml"
    assert p.is_file()
    first = p.read_text(encoding="utf-8")
    r2 = client.post("/api/projects", json=body)
    assert r2.status_code == 200
    assert r2.json()["created"] is False
    assert p.read_text(encoding="utf-8") == first


def test_get_agents_includes_department_after_seed(client) -> None:
    client.post(
        "/api/projects",
        json={
            "project_id": "p4-ag",
            "display_name": "Agents",
            "team_context": "hr",
        },
    )
    r = client.get("/api/agents", params={"project_id": "p4-ag"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    hit = next(x for x in items if x["agent_id"] == "onboarding")
    assert hit.get("department") == "HR"
    assert hit.get("icon_key") == "onboarding"
    review_hit = next(x for x in items if x["agent_id"] == "review")
    assert review_hit.get("department") == "HR"
    assert review_hit.get("icon_key") == "review"

    client.post(
        "/api/projects",
        json={
            "project_id": "p4-pmo",
            "display_name": "PMO",
            "team_context": "pmo",
        },
    )
    r2 = client.get("/api/agents", params={"project_id": "p4-pmo"})
    assert r2.status_code == 200
    items2 = r2.json()["items"]
    hit2 = next(x for x in items2 if x["agent_id"] == "project-ops")
    assert hit2.get("department") == "PMO"
    assert hit2.get("icon_key") == "project-ops"
    review_hit2 = next(x for x in items2 if x["agent_id"] == "review")
    assert review_hit2.get("department") == "PMO"
    assert review_hit2.get("icon_key") == "review"

    client.post(
        "/api/projects",
        json={
            "project_id": "p4-mkt2",
            "display_name": "MKT",
            "team_context": "marketing",
        },
    )
    r3 = client.get("/api/agents", params={"project_id": "p4-mkt2"})
    assert r3.status_code == 200
    items3 = r3.json()["items"]
    hit3 = next(x for x in items3 if x["agent_id"] == "marketing-copy")
    assert hit3.get("department") == "Marketing"
    assert hit3.get("icon_key") == "marketing-copy"
    review_hit3 = next(x for x in items3 if x["agent_id"] == "review")
    assert review_hit3.get("department") == "Marketing"
    assert review_hit3.get("icon_key") == "review"


def test_patch_project_team_context_triggers_seed(client) -> None:
    client.post(
        "/api/projects",
        json={"project_id": "p4-patch", "display_name": "P", "team_context": "developer"},
    )
    yaml_path = project_workspace("p4-patch") / "agents" / "software-architecture.yaml"
    assert not yaml_path.is_file()
    r = client.patch(
        "/api/projects/p4-patch",
        json={"team_context": "engineering"},
    )
    assert r.status_code == 200
    assert r.json()["team_context"] == "engineering"
    assert yaml_path.is_file()


def test_ensure_seed_team_projects_copies_agents(monkeypatch, tmp_path) -> None:
    import src.infrastructure.workspace as ws

    root = tmp_path / "data"
    root.mkdir()
    monkeypatch.setattr(ws, "DATA_ROOT", root)
    monkeypatch.delenv("STRANDS_SKIP_SEED_PROJECTS", raising=False)
    ensure_seed_team_projects()
    mkt = project_workspace("team-marketing") / "agents" / "marketing-copy.yaml"
    assert mkt.is_file()
    mkt2 = project_workspace("team-marketing") / "agents" / "review.yaml"
    assert mkt2.is_file()
    hr = project_workspace("team-hr") / "agents" / "review.yaml"
    assert hr.is_file()
    pmo = project_workspace("team-pmo") / "agents" / "review.yaml"
    assert pmo.is_file()
    eng = project_workspace("team-engineering") / "agents" / "software-architecture.yaml"
    assert eng.is_file()
