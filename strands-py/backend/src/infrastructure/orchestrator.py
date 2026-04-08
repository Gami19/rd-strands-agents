"""オーケストレータ + specialist（Agents as Tools）。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from strands import Agent, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel
from strands.vended_plugins.skills import AgentSkills

from src.config.prompts import ORCHESTRATOR_PROMPT, build_specialist_system_prompt
from src.infrastructure.agent_definitions import OrchestratorDefinition
from src.infrastructure.agent_factory import STATE_KEY, YAML_AGENT_CONTEXT_RULES, bedrock_model_from_env
from src.infrastructure.skill_policy import build_selected_skills_root
from src.infrastructure.tool_input_guard import build_default_tool_hooks
from src.infrastructure.tools_provider import (
    build_strands_file_io_tools,
    build_strands_restricted_tools_for_allowed,
)

logger = logging.getLogger(__name__)


def _specialist_agent(
    model: BedrockModel | None,
    ws: Path,
    skills_root: Path,
    tools: list[Any],
    name: str,
    role_instructions: str,
) -> Agent:
    system_prompt = build_specialist_system_prompt(
        name=name,
        role_instructions=role_instructions,
        workspace_root=ws,
        allow_handoff=False,
    )
    plugin = AgentSkills(skills=str(skills_root.resolve()), state_key=STATE_KEY)
    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
        per_turn=True,
    )
    kwargs: dict[str, Any] = {
        "system_prompt": system_prompt,
        "plugins": [plugin],
        "tools": tools,
        "conversation_manager": conversation_manager,
        "callback_handler": None,
        "hooks": build_default_tool_hooks(),
    }
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)


def _invoke_specialist(agent: Agent, label: str, query: str) -> str:
    try:
        out = agent(query)
        return str(out)
    except Exception as e:
        logger.exception("%s specialist failed", label)
        return f"[{label}] 実行中にエラーが発生しました: {e}"


def build_orchestrator_agent(
    workspace_root: Path,
    skills_root: Path,
    *,
    specialist_query_prefix: str = "",
    initial_messages: list[Any] | None = None,
) -> Agent:
    ws = workspace_root.resolve()
    model = bedrock_model_from_env()
    tools = build_strands_file_io_tools(workspace_root=ws, include_file_write=True)
    pfx = (specialist_query_prefix or "").strip()

    @tool
    def consult_distill(query: str) -> str:
        """要件・inbox/notes 蒸留、ドメインモデル、ストーリーマップ、仕様の構造化。入力はユーザーの目的をそのまま渡す。"""
        sp = _specialist_agent(
            model,
            ws,
            skills_root,
            tools,
            "distill",
            "Distill / story-map 系スキルを優先し、ソースをファイル根拠に整理する。",
        )
        q = f"{pfx}\n\n{query}" if pfx else query
        return _invoke_specialist(sp, "distill", q)

    @tool
    def consult_architecture(query: str) -> str:
        """システムアーキテクチャ、データ設計、図、ADR、フロー設計。入力はユーザーの目的をそのまま渡す。"""
        sp = _specialist_agent(
            model,
            ws,
            skills_root,
            tools,
            "architecture",
            "software-architecture / diagram / data-arch / 関連スキルで設計・図・トレードオフを整理する。",
        )
        q = f"{pfx}\n\n{query}" if pfx else query
        return _invoke_specialist(sp, "architecture", q)

    @tool
    def consult_review(query: str) -> str:
        """コード・設計・成果物のレビュー、テスト観点、品質チェック。入力はユーザーの目的をそのまま渡す。"""
        sp = _specialist_agent(
            model,
            ws,
            skills_root,
            tools,
            "review",
            "review / test / data-validation 等で指摘と改善案を出す。",
        )
        q = f"{pfx}\n\n{query}" if pfx else query
        return _invoke_specialist(sp, "review", q)

    okw: dict[str, Any] = {
        "system_prompt": ORCHESTRATOR_PROMPT,
        "tools": [consult_distill, consult_architecture, consult_review],
        "callback_handler": None,
    }
    if model is not None:
        okw["model"] = model
    if initial_messages:
        okw["messages"] = initial_messages
    return Agent(**okw)


def build_orchestrator_agent_from_definition(
    workspace_root: Path,
    skills_root: Path,
    definition: OrchestratorDefinition,
    *,
    specialist_query_prefix: str = "",
    initial_messages: list[Any] | None = None,
) -> Agent:
    ws = workspace_root.resolve()
    sr = skills_root.resolve()
    if definition.skills:
        sr = build_selected_skills_root(sr, definition.skills).resolve()
    model = bedrock_model_from_env()
    shared_tools = build_strands_restricted_tools_for_allowed(
        workspace_root=ws,
        allowed_tools=definition.allowed_tools,
    )
    dynamic_tools: list[Any] = []
    pfx = (specialist_query_prefix or "").strip()

    for spec in definition.specialists:

        def _make_tool(spec_ref=spec, prefix=pfx):
            def dynamic_consult(query: str) -> str:
                sp = _specialist_agent(
                    model,
                    ws,
                    sr,
                    shared_tools,
                    spec_ref.name,
                    spec_ref.role_instructions,
                )
                q = f"{prefix}\n\n{query}" if prefix else query
                return _invoke_specialist(sp, spec_ref.name, q)

            dynamic_consult.__name__ = spec_ref.tool_name
            dynamic_consult.__doc__ = (
                f"Specialist「{spec_ref.name}」へ委譲する。ユーザーの目的を query にそのまま渡す。"
            )
            return tool(dynamic_consult)

        dynamic_tools.append(_make_tool())

    okw: dict[str, Any] = {
        "system_prompt": f"{YAML_AGENT_CONTEXT_RULES}\n\n{definition.system_prompt}",
        "tools": dynamic_tools,
        "callback_handler": None,
    }
    if model is not None:
        okw["model"] = model
    if initial_messages:
        okw["messages"] = initial_messages
    return Agent(**okw)
