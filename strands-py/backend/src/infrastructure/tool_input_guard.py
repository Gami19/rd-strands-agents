"""Strands BeforeToolCallEvent で file_read / file_write / workspace_list の引数を検証する。

strands.event_loop.streaming の handle_content_block_stop では、ツール入力 JSON の
json.loads に失敗すると input が空の dict になる。未定義引数でツールが呼ばれ
例外や分かりにくいエラーになるのを防ぐ。

参考: strands.hooks.BeforeToolCallEvent（cancel_tool でツール結果として返せる）
"""

from __future__ import annotations

import json
import logging
from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

logger = logging.getLogger(__name__)


def _coerce_tool_input_dict(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _nonempty_str(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    return bool(str(v).strip())


class ToolInputGuardHook(HookProvider):
    """file_read / file_write / workspace_list の実行直前に必須フィールドを検証する。"""

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._guard)

    def _guard(self, event: BeforeToolCallEvent) -> None:
        tu = event.tool_use or {}
        name = str(tu.get("name") or "")
        if name not in ("file_read", "file_write", "workspace_list"):
            return

        raw_inp = tu.get("input")
        inp = _coerce_tool_input_dict(raw_inp)

        if inp is None or not inp:
            event.cancel_tool = (
                f"{name}: ツール入力が空か、JSON として解釈できません。"
                "モデルが出力した tool_use の input を確認してください。"
            )
            logger.warning("tool_input_guard: rejected %s (empty or unparseable input)", name)
            return

        if name == "file_read":
            if not _nonempty_str(inp.get("area")) or not _nonempty_str(inp.get("relative_path")):
                event.cancel_tool = (
                    "file_read: area と relative_path（空でない文字列）が必須です。"
                )
                logger.warning("tool_input_guard: rejected file_read missing area/relative_path")
            return

        if name == "workspace_list":
            if not _nonempty_str(inp.get("area")):
                event.cancel_tool = "workspace_list: area は必須です。"
                logger.warning("tool_input_guard: rejected workspace_list missing area")
                return
            rp = inp.get("relative_path")
            if _nonempty_str(rp):
                from src.infrastructure.workspace_paths import (
                    normalize_workspace_relative_filename,
                )

                try:
                    normalize_workspace_relative_filename(str(rp))
                except ValueError as e:
                    event.cancel_tool = f"workspace_list: {e}"
                    logger.warning("tool_input_guard: rejected workspace_list bad relative_path")
            return

        if name == "file_write":
            if not _nonempty_str(inp.get("area")) or not _nonempty_str(inp.get("relative_path")):
                event.cancel_tool = (
                    "file_write: area と relative_path（空でない文字列）が必須です。"
                )
                logger.warning("tool_input_guard: rejected file_write missing area/relative_path")
                return
            if "content" not in inp or not isinstance(inp.get("content"), str):
                event.cancel_tool = (
                    "file_write: content は文字列である必要があります（空文字は可）。"
                )
                logger.warning("tool_input_guard: rejected file_write missing/wrong content type")
                return


def build_default_tool_hooks() -> list[HookProvider]:
    return [ToolInputGuardHook()]
