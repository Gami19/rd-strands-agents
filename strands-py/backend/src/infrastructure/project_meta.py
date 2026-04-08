"""プロジェクト workspace 直下のメタデータ（.strands-project.json）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.infrastructure.team_context import normalize_team_context

META_FILENAME = ".strands-project.json"


class ProjectMetaJsonError(Exception):
    """メタファイルが存在するが JSON として解釈できない。"""

    def __init__(self, path: Path, message: str = "JSON の構文が無効です") -> None:
        self.path = path
        super().__init__(message)


def read_meta_dict(workspace_root: Path) -> dict[str, Any]:
    """メタファイルが無ければ空 dict。ファイルありでパース不能なら ProjectMetaJsonError。"""
    path = workspace_root.resolve() / META_FILENAME
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ProjectMetaJsonError(path, f"メタを読めません: {e}") from e
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ProjectMetaJsonError(
            path,
            f".strands-project.json の JSON が壊れています。ファイルを修正するか削除してください: {e}",
        ) from e
    if not isinstance(data, dict):
        raise ProjectMetaJsonError(path, ".strands-project.json のルートはオブジェクトである必要があります")
    return data


def _write_meta_dict(workspace_root: Path, data: dict[str, Any]) -> None:
    path = workspace_root.resolve() / META_FILENAME
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_team_context(workspace_root: Path) -> str:
    data = read_meta_dict(workspace_root)
    return normalize_team_context(data.get("team_context"))


def read_display_name(workspace_root: Path, *, fallback_id: str) -> str:
    try:
        data = read_meta_dict(workspace_root)
    except ProjectMetaJsonError:
        raise
    dn = data.get("display_name")
    if isinstance(dn, str):
        s = dn.strip()
        if s:
            return s
    return fallback_id


def write_display_name(workspace_root: Path, display_name: str) -> None:
    data = read_meta_dict(workspace_root)
    data["display_name"] = display_name
    _write_meta_dict(workspace_root, data)


def write_team_context(workspace_root: Path, team_context: str) -> None:
    data = read_meta_dict(workspace_root)
    data["team_context"] = normalize_team_context(team_context)
    _write_meta_dict(workspace_root, data)


def write_project_meta(
    workspace_root: Path,
    *,
    display_name: str | None = None,
    team_context: str | None = None,
) -> None:
    data = read_meta_dict(workspace_root)
    if display_name is not None:
        data["display_name"] = display_name
    if team_context is not None:
        data["team_context"] = normalize_team_context(team_context)
    _write_meta_dict(workspace_root, data)
