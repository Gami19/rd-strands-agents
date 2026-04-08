"""Swarm（handoff 協調）と Skills 専門エージェント。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel
from strands.multiagent import Swarm
from strands.vended_plugins.skills import AgentSkills

from src.config.prompts import (
    COORDINATOR_PROMPT,
    build_specialist_system_prompt,
    build_yaml_swarm_coordinator_prompt,
)
from src.infrastructure.agent_definitions import load_single_agent_definition, normalize_agent_id
from src.infrastructure.agent_factory import STATE_KEY, bedrock_model_from_env, build_skills_agent_from_yaml
from src.infrastructure.tool_input_guard import build_default_tool_hooks
from src.infrastructure.skill_policy import build_filtered_skills_root
from src.infrastructure.tools_provider import build_strands_file_io_tools


def _skills_specialist(
    model: BedrockModel | None,
    ws: Path,
    skills_root: Path,
    tools: list[Any],
    name: str,
    role_instructions: str,
    *,
    system_prompt_suffix: str = "",
) -> Agent:
    base_prompt = build_specialist_system_prompt(
        name=name,
        role_instructions=role_instructions,
        workspace_root=ws,
    )
    system_prompt = base_prompt + (system_prompt_suffix or "")
    plugin = AgentSkills(skills=str(skills_root.resolve()), state_key=STATE_KEY)
    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
        per_turn=True,
    )
    kwargs: dict[str, Any] = {
        "name": name,
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


def build_swarm(
    workspace_root: Path,
    skills_root: Path,
    *,
    workspace_context_suffix: str = "",
    coordinator_initial_messages: list[Any] | None = None,
) -> Swarm:
    if not skills_root.is_dir():
        raise ValueError("swarm モードには有効な skills_root が必要です")
    effective_skills_root = build_filtered_skills_root(skills_root)

    ws = workspace_root.resolve()
    model = bedrock_model_from_env()
    tools = build_strands_file_io_tools(workspace_root=ws, include_file_write=True)
    sp_suffix = ""
    s = (workspace_context_suffix or "").strip()
    if s:
        sp_suffix = f"\n\n---\n【Workspace 目次（当リクエスト）】\n{s}"

    ckw: dict[str, Any] = {
        "name": "coordinator",
        "system_prompt": COORDINATOR_PROMPT,
        "callback_handler": None,
    }
    if model is not None:
        ckw["model"] = model
    if coordinator_initial_messages:
        ckw["messages"] = coordinator_initial_messages
    coordinator = Agent(**ckw)

    distill = _skills_specialist(
        model,
        ws,
        effective_skills_root,
        tools,
        "distill",
        "Distill / story-map 系スキルを優先し、ソースをファイル根拠に整理する。",
        system_prompt_suffix=sp_suffix,
    )
    architecture = _skills_specialist(
        model,
        ws,
        effective_skills_root,
        tools,
        "architecture",
        "software-architecture / diagram / data-arch / 関連スキルで設計・図・トレードオフを整理する。",
        system_prompt_suffix=sp_suffix,
    )
    review = _skills_specialist(
        model,
        ws,
        effective_skills_root,
        tools,
        "review",
        "review / test / data-validation 等で指摘と改善案を出す。",
        system_prompt_suffix=sp_suffix,
    )

    return Swarm(
        [coordinator, distill, architecture, review],
        entry_point=coordinator,
        max_handoffs=20,
        max_iterations=20,
        repetitive_handoff_detection_window=8,
        repetitive_handoff_min_unique_agents=3,
    )


def build_swarm_from_workspace_agent_ids(
    workspace_root: Path,
    skills_root: Path,
    agent_ids: list[str],
    *,
    workspace_context_suffix: str = "",
    coordinator_initial_messages: list[Any] | None = None,
) -> Swarm:
    if not skills_root.is_dir():
        raise ValueError("swarm モードには有効な skills_root が必要です")
    if len(agent_ids) < 2:
        raise ValueError("agent_ids は2件以上必要です")

    effective_skills_root = build_filtered_skills_root(skills_root)
    ws = workspace_root.resolve()
    model = bedrock_model_from_env()

    entries: list[tuple[str, str]] = []
    specialists: list[Agent] = []
    for raw_id in agent_ids:
        aid = normalize_agent_id(raw_id)
        definition = load_single_agent_definition(ws, aid)
        entries.append((aid, definition.name))
        specialists.append(
            build_skills_agent_from_yaml(
                workspace_root=ws,
                skills_root=effective_skills_root,
                agent_id=aid,
                filtered_skills_root=effective_skills_root,
                swarm_node_name=aid,
                workspace_context_suffix=workspace_context_suffix,
            )
        )

    coord_prompt = build_yaml_swarm_coordinator_prompt(entries)
    ckw: dict[str, Any] = {
        "name": "coordinator",
        "system_prompt": coord_prompt,
        "callback_handler": None,
    }
    if model is not None:
        ckw["model"] = model
    if coordinator_initial_messages:
        ckw["messages"] = coordinator_initial_messages
    coordinator = Agent(**ckw)

    return Swarm(
        [coordinator, *specialists],
        entry_point=coordinator,
        max_handoffs=20,
        max_iterations=20,
        repetitive_handoff_detection_window=8,
        repetitive_handoff_min_unique_agents=3,
    )

