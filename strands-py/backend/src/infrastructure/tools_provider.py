from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any

from strands import tool

from src.infrastructure.compat_tools import build_compat_tools
from src.infrastructure.workspace_paths import resolve_workspace_area_path

logger = logging.getLogger(__name__)


def _as_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _is_denied_path(p: Path) -> bool:
    deny_dir_markers = ("/.git/", "/node_modules/", "/__pycache__/")
    deny_suffixes = (".pem",)
    name_lower = p.name.lower()
    if name_lower.startswith(".env"):
        return True
    if "id_rsa" in name_lower:
        return True
    if "credentials" in name_lower:
        return True
    if p.suffix.lower() in deny_suffixes:
        return True
    as_posix_lower = p.as_posix().lower()
    return any(m in f"/{as_posix_lower.strip('/')}/" for m in deny_dir_markers)


def _make_restricted_file_read_tool(workspace_root: Path):
    ws = workspace_root.resolve()

    @tool
    def file_read(area: str, relative_path: str, start_line: int = 1, end_line: int = 0) -> str:
        """
        workspace 内の inbox / notes / proposal / decision / agents のいずれかから
        UTF-8 テキストを読み取る。relative_path はファイル名のみ（サブディレクトリ不可）。
        """
        try:
            resolved = resolve_workspace_area_path(
                ws, area, relative_path, action="読み取り"
            )
            if not resolved.is_file():
                raise ValueError(f"ファイルが見つかりません: {area}/{relative_path}")
            if _is_denied_path(resolved):
                raise ValueError("このパスは読み取り禁止です")

            size = resolved.stat().st_size
            if size > 10 * 1024 * 1024:
                raise ValueError(
                    "ファイルが大きすぎます（10MB 超）。分割するか、必要箇所のみを別ファイルに抜粋してください。"
                )

            try:
                start = int(start_line)
            except Exception:
                start = 1
            try:
                end = int(end_line)
            except Exception:
                end = 0
            if start < 1:
                start = 1
            if end != 0 and end < start:
                end = start

            text = resolved.read_text(encoding="utf-8", errors="replace")
            if start == 1 and end == 0:
                logger.info(
                    "file_read ok area=%s relative_path=%s chars=%s (full file)",
                    area,
                    relative_path,
                    len(text),
                )
                return text

            lines = text.splitlines(keepends=True)
            s_idx = start - 1
            e_idx = len(lines) if end == 0 else min(len(lines), end)
            snippet = "".join(lines[s_idx:e_idx])
            logger.info(
                "file_read ok area=%s relative_path=%s chars=%s start_line=%s end_line=%s",
                area,
                relative_path,
                len(snippet),
                start,
                end,
            )
            return snippet
        except Exception as e:
            out = _as_json(
                {
                    "status": "error",
                    "tool": "file_read",
                    "reason": str(e),
                    "area": area,
                    "relative_path": relative_path,
                }
            )
            logger.info("file_read result=%s", out)
            return out

    return file_read


def _make_utf8_file_write_tool(workspace_root: Path):
    """workspace 制限付きの file_write。領域（area）と相対パスで保存先を指定。常に UTF-8。"""
    ws = workspace_root.resolve()
    allowed_write_roots = {
        (ws / "inbox").resolve(),
        (ws / "notes").resolve(),
        (ws / "proposal").resolve(),
        (ws / "decision").resolve(),
        (ws / "agents").resolve(),
    }
    for d in allowed_write_roots:
        d.mkdir(parents=True, exist_ok=True)

    @tool
    def file_write(area: str, relative_path: str, content: str) -> str:
        """
        inbox / notes / proposal / decision / agents のいずれかへ UTF-8 で保存する。
        relative_path はファイル名のみ（サブディレクトリ不可）。
        """
        try:
            resolved = resolve_workspace_area_path(
                ws, area, relative_path, action="書き込み"
            )
            if _is_denied_path(resolved):
                raise ValueError("このパスは書き込み禁止です")

            parent = resolved.parent.resolve()
            if not any(
                parent == r or parent.is_relative_to(r) for r in allowed_write_roots
            ):
                raise ValueError(
                    "書き込み先は inbox/ notes/ proposal/ decision/ agents 配下のみ対応しています"
                )

            if resolved.exists() and not resolved.is_file():
                raise ValueError("ファイル以外には書き込めません")

            data = content if isinstance(content, str) else str(content)
            size_bytes = len(data.encode("utf-8", errors="replace"))
            max_bytes = 100 * 1024 * 1024
            if size_bytes > max_bytes:
                raise ValueError(
                    f"書き込み内容が大きすぎます（{max_bytes // (1024 * 1024)}MB まで）。分割してください。"
                )

            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(data, encoding="utf-8")
            out = _as_json(
                {
                    "status": "ok",
                    "tool": "file_write",
                    "output": str(resolved),
                    "bytes": size_bytes,
                    "exists": resolved.is_file(),
                }
            )
            logger.info("file_write result=%s", out)
            return out
        except Exception as e:
            out = _as_json(
                {
                    "status": "error",
                    "tool": "file_write",
                    "reason": str(e),
                    "area": area,
                    "relative_path": relative_path,
                }
            )
            logger.info("file_write result=%s", out)
            return out

    return file_write


def build_strands_file_io_tools(*, workspace_root: Path, include_file_write: bool) -> list[Any]:
    """
    Strands の tool へ `file_read` / `file_write` を注入する共通部分。

    file_read/file_write ともに自前実装を使い、挙動を全モードで統一する。
    順序は従来通り file_read, file_write, compat_tools。
    """

    from src.infrastructure.workspace_catalog import make_workspace_list_tool

    compat_tools = build_compat_tools(workspace_root)
    wl = make_workspace_list_tool(workspace_root)
    if include_file_write:
        return [
            _make_restricted_file_read_tool(workspace_root),
            _make_utf8_file_write_tool(workspace_root),
            wl,
            *compat_tools,
        ]
    return [
        _make_restricted_file_read_tool(workspace_root),
        wl,
        *compat_tools,
    ]


def build_strands_restricted_file_read_tools(*, workspace_root: Path) -> list[Any]:
    from src.infrastructure.workspace_catalog import make_workspace_list_tool

    return [
        _make_restricted_file_read_tool(workspace_root),
        make_workspace_list_tool(workspace_root),
    ]


def build_strands_restricted_tools_for_allowed(
    *,
    workspace_root: Path,
    allowed_tools: tuple[str, ...],
) -> list[Any]:
    from src.infrastructure.workspace_catalog import make_workspace_list_tool

    allow = set(allowed_tools)

    tools: list[Any] = []

    if "file_read" in allow:
        tools.append(_make_restricted_file_read_tool(workspace_root))
        tools.append(make_workspace_list_tool(workspace_root))

    if "file_write" in allow:
        tools.append(_make_utf8_file_write_tool(workspace_root))

    compat = build_compat_tools(workspace_root.resolve())
    for t in compat:
        name = getattr(t, "__name__", "") or ""
        if name and name in allow:
            tools.append(t)

    return tools


__all__ = [
    "build_strands_file_io_tools",
    "build_strands_restricted_file_read_tools",
    "build_strands_restricted_tools_for_allowed",
]
