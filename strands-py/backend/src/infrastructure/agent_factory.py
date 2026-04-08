"""Strands Agent の組み立て（Bedrock は公式ドキュメントの BedrockModel 利用パターンに準拠）。"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.vended_plugins.skills import AgentSkills
from strands.models import BedrockModel

from src.config.prompts import build_skills_system_prompt
from src.infrastructure.agent_definitions import (
    load_orchestrator_definition,
    load_single_agent_definition,
    normalize_agent_id,
)
from src.infrastructure.skill_policy import build_filtered_skills_root, build_selected_skills_root
from src.infrastructure.tool_input_guard import build_default_tool_hooks
from src.infrastructure.tools_provider import (
    build_strands_file_io_tools,
    build_strands_restricted_tools_for_allowed,
)

STATE_KEY = "agent_skills"

logger = logging.getLogger(__name__)

DEFAULT_BEDROCK_READ_TIMEOUT_S = 300


YAML_AGENT_CONTEXT_RULES = """以下は UI で agent_id を選択した「YAML エージェント」モードのルールです。

- あなたは KC のスキル（AgentSkills / SKILL.md）を「選んで実行している」前提で説明してはいけません。
- 「effective-typescript スキル」「review スキル」など、KC スキル名を要件整理や説明に持ち出さないでください。
- できることは、この YAML の system_prompt と allowed_tools によって決まります。allowed_tools に無いツールは使えません。
- 出力は必要なら file_write で保存できます（許可されている場合）。area は用途に応じ agents / notes / inbox / proposal / decision から選ぶ。
- file_read / file_write では area と relative_path を必須とする（空で呼ばない）。file_write では content も必須。
- relative_path は該当 area 直下のファイル名のみ（サブディレクトリ・パス区切り・.. 不可。area 名を含めない）。
  例: agents の定義は area=\"agents\", relative_path=\"my-id.yaml\"（YAML の id とファイル名を一致）。
- 一覧・詳細は workspace_list(area) または workspace_list(area, relative_path)。file_read と同じ領域のみ。
"""

YAML_SWARM_HANDOFF_RULES = """---
【Swarm / マルチエージェント（Workspace で agents を複数参照したとき）】
coordinator と他エージェントと同一 Swarm に参加している場合は次を守る。
- 連携や会話の続きには **handoff_to_agent** で相手へ制御を渡す。`agent_name` には対象のエージェント id（YAML の id）または **coordinator** を正確に指定する。
- 本文だけで「次は相手の番」等と書いて終えない。次に応答すべき相手がいれば **handoff_to_agent を呼ぶ**。
- ユーザーの依頼が完了し、他エージェントへの追加タスクが不要なら **coordinator** に返してよい。"""


def _bedrock_client_config_from_env() -> Config:
    read_raw = os.getenv("AWS_BEDROCK_READ_TIMEOUT", "").strip()
    if read_raw:
        try:
            read_timeout = int(read_raw)
            if read_timeout <= 0:
                raise ValueError
        except ValueError:
            logger.warning(
                "Invalid AWS_BEDROCK_READ_TIMEOUT=%r; using default %s",
                read_raw,
                DEFAULT_BEDROCK_READ_TIMEOUT_S,
            )
            read_timeout = DEFAULT_BEDROCK_READ_TIMEOUT_S
    else:
        read_timeout = DEFAULT_BEDROCK_READ_TIMEOUT_S

    cfg_kwargs: dict[str, Any] = {"read_timeout": read_timeout}
    connect_raw = os.getenv("AWS_BEDROCK_CONNECT_TIMEOUT", "").strip()
    if connect_raw:
        try:
            connect_timeout = int(connect_raw)
            if connect_timeout <= 0:
                raise ValueError
            cfg_kwargs["connect_timeout"] = connect_timeout
        except ValueError:
            logger.warning(
                "Invalid AWS_BEDROCK_CONNECT_TIMEOUT=%r; ignoring",
                connect_raw,
            )

    return Config(**cfg_kwargs)


def bedrock_model_from_env() -> BedrockModel | None:
    model_id = os.getenv("AWS_BEDROCK_MODEL_ID", "").strip()
    if not model_id:
        return None

    region = (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-west-2"
    ).strip()
    key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

    model_config: dict[str, Any] = {"model_id": model_id, "region_name": region}
    max_tokens_raw = os.getenv("AWS_MAX_TOKENS", "").strip()
    if max_tokens_raw:
        try:
            model_config["max_tokens"] = int(max_tokens_raw)
        except ValueError:
            pass

    if key and secret:
        session = boto3.Session(
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            region_name=region,
        )
        model_config["boto_session"] = session
        model_config.pop("region_name", None)

    model_config["boto_client_config"] = _bedrock_client_config_from_env()

    return BedrockModel(**model_config)


def build_skills_agent_from_yaml(
    *,
    workspace_root: Path,
    skills_root: Path,
    agent_id: str,
    filtered_skills_root: Path | None = None,
    swarm_node_name: str | None = None,
    workspace_context_suffix: str = "",
    initial_messages: list[Any] | None = None,
) -> Agent:
    """
    kind=single の YAML から Agent を組み立てる。
    swarm_node_name を渡したときは Swarm のノード用（handoff 名と一致させる）。
    """
    ws = workspace_root.resolve()
    aid = normalize_agent_id(agent_id)
    definition = load_single_agent_definition(ws, aid)
    base_path = filtered_skills_root if filtered_skills_root is not None else skills_root
    if base_path is None or not base_path.is_dir():
        raise ValueError("skills_root が未設定です")
    skills_path = base_path
    if definition.skills:
        skills_path = build_selected_skills_root(skills_path, definition.skills)
    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
        per_turn=True,
    )
    tools = build_strands_restricted_tools_for_allowed(
        workspace_root=ws,
        allowed_tools=definition.allowed_tools,
    )
    plugin = AgentSkills(
        skills=str(skills_path.resolve()),
        state_key=STATE_KEY,
    )
    sp = f"{YAML_AGENT_CONTEXT_RULES}\n\n{definition.system_prompt}"
    if swarm_node_name:
        sp = f"{sp}\n\n{YAML_SWARM_HANDOFF_RULES}"
    s = (workspace_context_suffix or "").strip()
    if s:
        sp = f"{sp}\n\n---\n【Workspace 目次（当リクエスト）】\n{s}"
    kwargs: dict[str, Any] = {
        "plugins": [plugin],
        "tools": tools,
        "conversation_manager": conversation_manager,
        "system_prompt": sp,
        "hooks": build_default_tool_hooks(),
    }
    if swarm_node_name:
        kwargs["name"] = normalize_agent_id(swarm_node_name)
        kwargs["callback_handler"] = None
    model = bedrock_model_from_env()
    if model is not None:
        kwargs["model"] = model
    if initial_messages:
        kwargs["messages"] = initial_messages
    return Agent(**kwargs)


def build_agent(
    *,
    mode: str = "default",
    workspace_root: Path | None = None,
    skills_root: Path | None = None,
    agent_id: str | None = None,
    specialist_query_prefix: str = "",
    initial_messages: list[Any] | None = None,
) -> Agent:
    """
    mode=default: 通常チャット（Skills プラグインなし）。
    mode=skills: AgentSkills + file_read / file_write（1 エージェント最小構成）。
    mode=orchestrate: オーケストレータ + specialist（Agents as Tools）。API 互換用。Web UI では未使用。
    """

    filtered_skills_root: Path | None = None
    if mode in ("skills", "orchestrate"):
        if not skills_root or not skills_root.is_dir():
            raise ValueError(f"{mode} モードには有効な skills_root が必要です")
        filtered_skills_root = build_filtered_skills_root(skills_root)

    if mode == "orchestrate":
        from src.infrastructure.orchestrator import (
            build_orchestrator_agent,
            build_orchestrator_agent_from_definition,
        )

        ws_orch = (workspace_root or Path.cwd()).resolve()
        if agent_id:
            orch_def = load_orchestrator_definition(ws_orch, agent_id)
            return build_orchestrator_agent_from_definition(
                ws_orch,
                filtered_skills_root or skills_root,
                orch_def,
                specialist_query_prefix=specialist_query_prefix,
                initial_messages=initial_messages,
            )
        return build_orchestrator_agent(
            ws_orch,
            filtered_skills_root or skills_root,
            specialist_query_prefix=specialist_query_prefix,
            initial_messages=initial_messages,
        )

    model = bedrock_model_from_env()

    if mode == "skills":
        ws = (workspace_root or Path.cwd()).resolve()
        if agent_id:
            return build_skills_agent_from_yaml(
                workspace_root=ws,
                skills_root=filtered_skills_root or skills_root,  # type: ignore[arg-type]
                agent_id=agent_id,
                filtered_skills_root=filtered_skills_root,
                initial_messages=initial_messages,
            )

        system_prompt = build_skills_system_prompt(ws)
        plugin = AgentSkills(
            skills=str((filtered_skills_root or skills_root).resolve()),
            state_key=STATE_KEY,
        )
        conversation_manager = SlidingWindowConversationManager(
            window_size=20,
            should_truncate_results=True,
            per_turn=True,
        )
        tools = build_strands_file_io_tools(workspace_root=ws, include_file_write=True)
        kwargs: dict[str, Any] = {
            "plugins": [plugin],
            "tools": tools,
            "conversation_manager": conversation_manager,
            "system_prompt": system_prompt,
            "hooks": build_default_tool_hooks(),
        }
        if model is not None:
            kwargs["model"] = model
        if initial_messages:
            kwargs["messages"] = initial_messages
        return Agent(**kwargs)

    if model is not None:
        return Agent(model=model, messages=initial_messages or [])
    if initial_messages:
        return Agent(messages=initial_messages)
    return Agent()

