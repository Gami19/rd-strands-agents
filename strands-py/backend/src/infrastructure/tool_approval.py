from __future__ import annotations

from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


class ToolApprovalHook(HookProvider):
    def __init__(self, *, app_name: str, approval_tools: set[str]) -> None:
        self.app_name = app_name
        self.approval_tools = set(approval_tools)

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._approve)

    def _approve(self, event: BeforeToolCallEvent) -> None:
        tool_use = event.tool_use or {}
        name = str(tool_use.get("name") or "")
        if not name or name not in self.approval_tools:
            return

        approval = event.interrupt(
            f"{self.app_name}-tool-approval",
            reason={
                "tool": name,
                "input": tool_use.get("input"),
            },
        )
        if str(approval).strip().lower() != "y":
            event.cancel_tool = "User denied tool permission"

