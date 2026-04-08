"""workspace 目次の生成（REST・workspace_list ツール・チャット注入で共有）。"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.infrastructure.agent_definitions import list_agent_definitions
from src.infrastructure.workspace_paths import (
    WORKSPACE_AREAS,
    normalize_area,
    normalize_workspace_relative_filename,
    resolve_workspace_area_path,
)

logger = logging.getLogger(__name__)

MAX_SUMMARY_LINES_PER_AREA = 15
MAX_SUMMARY_CHARS_PER_AREA = 2000
MAX_SUMMARY_TOTAL_CHARS = 8000
MAX_TOOL_JSON_CHARS = 256 * 1024


def _iso_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _deny_catalog_file(p: Path) -> bool:
    name_lower = p.name.lower()
    if name_lower.startswith(".env"):
        return True
    if "id_rsa" in name_lower:
        return True
    if "credentials" in name_lower:
        return True
    if p.suffix.lower() == ".pem":
        return True
    return False


@dataclass(frozen=True)
class _FlatFileEntry:
    area: str
    relative_path: str
    display_name: str
    mtime: float
    size_bytes: int
    kind: str | None
    description: str | None


def _collect_non_agent_files(workspace: Path, area: str) -> list[_FlatFileEntry]:
    base = (workspace / area).resolve()
    if not base.is_dir():
        return []
    out: list[_FlatFileEntry] = []
    for p in base.iterdir():
        if not p.is_file() or _deny_catalog_file(p):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        name = p.name
        out.append(
            _FlatFileEntry(
                area=area,
                relative_path=name,
                display_name=name,
                mtime=st.st_mtime,
                size_bytes=st.st_size,
                kind=None,
                description=None,
            )
        )
    out.sort(key=lambda e: e.mtime, reverse=True)
    return out


def _collect_agent_entries(workspace: Path) -> list[_FlatFileEntry]:
    raw: list[_FlatFileEntry] = []
    for m in list_agent_definitions(workspace):
        p = m.source_path
        if not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        if _deny_catalog_file(p):
            continue
        desc = (m.description or "").strip()
        if len(desc) > 200:
            desc = desc[:197] + "..."
        raw.append(
            _FlatFileEntry(
                area="agents",
                relative_path=p.name,
                display_name=(m.name or m.agent_id).strip() or m.agent_id,
                mtime=st.st_mtime,
                size_bytes=st.st_size,
                kind=m.kind,
                description=desc or None,
            )
        )
    by_name: dict[str, _FlatFileEntry] = {}
    for e in raw:
        key = e.display_name
        prev = by_name.get(key)
        if prev is None or e.mtime > prev.mtime:
            by_name[key] = e
    deduped = list(by_name.values())
    deduped.sort(key=lambda e: e.mtime, reverse=True)
    return deduped


def collect_workspace_catalog_entries(workspace: Path) -> dict[str, list[_FlatFileEntry]]:
    """area ごとのエントリ（agents は同名 display_name は mtime 最新のみ）。"""
    ws = workspace.resolve()
    out: dict[str, list[_FlatFileEntry]] = {}
    for area in sorted(WORKSPACE_AREAS):
        if area == "agents":
            out[area] = _collect_agent_entries(ws)
        else:
            out[area] = _collect_non_agent_files(ws, area)
    return out


def build_workspace_catalog_payload(workspace: Path) -> dict[str, Any]:
    """REST / ツール用の JSON 互換 dict。"""
    by_area = collect_workspace_catalog_entries(workspace)
    areas_out: dict[str, Any] = {}
    for area, entries in by_area.items():
        rows: list[dict[str, Any]] = []
        for e in entries:
            row: dict[str, Any] = {
                "relative_path": e.relative_path,
                "display_name": e.display_name,
                "mtime": _iso_mtime(e.mtime),
                "size_bytes": e.size_bytes,
            }
            if area == "agents":
                row["agent_id"] = Path(e.relative_path).stem
            if e.kind:
                row["kind"] = e.kind
            if e.description:
                row["description"] = e.description
            rows.append(row)
        areas_out[area] = rows
    return {"areas": areas_out}


def _entry_to_json_row(e: _FlatFileEntry) -> dict[str, Any]:
    row: dict[str, Any] = {
        "area": e.area,
        "relative_path": e.relative_path,
        "display_name": e.display_name,
        "mtime": _iso_mtime(e.mtime),
        "size_bytes": e.size_bytes,
    }
    if e.area == "agents":
        row["agent_id"] = Path(e.relative_path).stem
    if e.kind:
        row["kind"] = e.kind
    if e.description:
        row["description"] = e.description
    return row


def workspace_list_resolve(
    workspace: Path,
    area: str,
    relative_path: str | None = None,
) -> dict[str, Any]:
    """workspace_list ツールのペイロード（status ok/error）。"""
    try:
        a = normalize_area(area)
    except ValueError as e:
        return {"status": "error", "tool": "workspace_list", "reason": str(e)}

    by_area = collect_workspace_catalog_entries(workspace.resolve())
    entries = by_area.get(a, [])

    if relative_path is None or not str(relative_path).strip():
        payload = {
            "status": "ok",
            "tool": "workspace_list",
            "area": a,
            "items": [_entry_to_json_row(e) for e in entries],
        }
        return payload

    try:
        name = normalize_workspace_relative_filename(relative_path)
    except ValueError as e:
        return {
            "status": "error",
            "tool": "workspace_list",
            "reason": str(e),
            "area": a,
        }

    for e in entries:
        if e.relative_path == name:
            return {
                "status": "ok",
                "tool": "workspace_list",
                "area": a,
                "items": [_entry_to_json_row(e)],
            }

    try:
        p = resolve_workspace_area_path(
            workspace.resolve(), a, name, action="一覧"
        )
        if p.is_file():
            st = p.stat()
            fe = _FlatFileEntry(
                area=a,
                relative_path=name,
                display_name=name,
                mtime=st.st_mtime,
                size_bytes=st.st_size,
                kind=None,
                description=None,
            )
            return {
                "status": "ok",
                "tool": "workspace_list",
                "area": a,
                "items": [_entry_to_json_row(fe)],
            }
    except (ValueError, OSError):
        pass

    return {
        "status": "error",
        "tool": "workspace_list",
        "reason": f"ファイルが見つかりません: {a}/{name}",
        "area": a,
        "relative_path": name,
    }


def format_workspace_index_block(workspace: Path) -> str:
    """チャット先頭に付与する要約テキスト。"""
    lines: list[str] = [
        "【Workspace 目次（要約）】",
        "ユーザが指す名前は次の display_name のみを手がかりにし、file_read / file_write では area と"
        " relative_path（ファイル名のみ）を一致させること。",
        "同名のエージェントが複数ある場合は mtime が最新の定義のみ此処に示す。",
        "打ち切られた場合は workspace_list(area) で詳細を取得すること。",
        "",
    ]
    by_area = collect_workspace_catalog_entries(workspace.resolve())
    total_budget = MAX_SUMMARY_TOTAL_CHARS
    used_total = 0

    for area in sorted(WORKSPACE_AREAS):
        entries = by_area.get(area, [])
        if not entries:
            continue
        header = f"[{area}]"
        area_lines = [header]
        area_chars = len(header) + 1
        line_count = 0
        truncated_area = False
        for e in entries:
            if line_count >= MAX_SUMMARY_LINES_PER_AREA:
                truncated_area = True
                break
            if area == "agents":
                desc = (e.description or "").replace("\n", " ").strip()
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                row = (
                    f"  - relative_path={json.dumps(e.relative_path, ensure_ascii=False)} "
                    f"display_name={json.dumps(e.display_name, ensure_ascii=False)} "
                    f"agent_id={json.dumps(Path(e.relative_path).stem, ensure_ascii=False)} "
                    f"kind={e.kind or 'single'}"
                    + (f" | {desc}" if desc else "")
                )
            else:
                row = (
                    f"  - relative_path={json.dumps(e.relative_path, ensure_ascii=False)} "
                    f"display_name={json.dumps(e.display_name, ensure_ascii=False)}"
                )
            if area_chars + len(row) + 1 > MAX_SUMMARY_CHARS_PER_AREA:
                truncated_area = True
                break
            if used_total + area_chars + len(row) + 1 > total_budget:
                truncated_area = True
                break
            area_lines.append(row)
            area_chars += len(row) + 1
            line_count += 1

        block = "\n".join(area_lines)
        if truncated_area:
            block += "\n  …（この area は要約を打ち切り。workspace_list で確認）"
        block += "\n"
        if used_total + len(block) > total_budget:
            lines.append("…（全体の要約を打ち切り。workspace_list で確認）\n")
            break
        lines.append(block)
        used_total += len(block)

    return "\n".join(lines).rstrip() + "\n"


def log_workspace_index_debug(
    *, project_id: str, workspace: Path, index_text: str
) -> None:
    data = collect_workspace_catalog_entries(workspace.resolve())
    counts = {a: len(v) for a, v in data.items()}
    h = hashlib.sha256(index_text.encode("utf-8", errors="replace")).hexdigest()
    logger.debug(
        "workspace_index project_id=%s counts=%s chars=%s sha256=%s",
        project_id,
        counts,
        len(index_text),
        h,
    )


def _json_trim_payload(payload: dict[str, Any]) -> str:
    if "items" not in payload:
        return json.dumps(payload, ensure_ascii=False)
    base = dict(payload)
    items = list(base.get("items") or [])
    while items:
        trial = {**base, "items": items}
        s = json.dumps(trial, ensure_ascii=False)
        if len(s) <= MAX_TOOL_JSON_CHARS:
            return s
        items.pop()
        base["truncated"] = True
    s = json.dumps({**base, "items": []}, ensure_ascii=False)
    if len(s) > MAX_TOOL_JSON_CHARS:
        return s[: max(0, MAX_TOOL_JSON_CHARS - 40)] + "…"
    return s


def make_workspace_list_tool(workspace_root: Path):
    from strands import tool

    ws = workspace_root.resolve()

    @tool
    def workspace_list(area: str, relative_path: str = "") -> str:
        """
        workspace 内のファイル一覧を返す。area は inbox / notes / proposal / decision / agents。
        relative_path を省略するとその area の全件。指定時はファイル名のみ（1 セグメント）。
        """
        rel = (relative_path or "").strip()
        payload = workspace_list_resolve(ws, area, rel if rel else None)
        return _json_trim_payload(payload)

    return workspace_list
