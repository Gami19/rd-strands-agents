from __future__ import annotations

import asyncio
import json
import logging
import uuid
import re
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from src.infrastructure.agent_definitions import load_orchestrator_definition, normalize_agent_id
from src.infrastructure.agent_factory import build_agent
from src.infrastructure.swarm_factory import build_swarm, build_swarm_from_workspace_agent_ids
from src.infrastructure.project_meta import ProjectMetaJsonError
from src.infrastructure.project_runtime import resolve_skills_for_project
from src.infrastructure.team_context import workflow_enabled
from src.infrastructure.workspace import ensure_project_workspace
from src.infrastructure.workspace_catalog import (
    format_workspace_index_block,
    log_workspace_index_debug,
)
from src.config.attachments import format_attachments_instruction

logger = logging.getLogger(__name__)

_INTERRUPT_SESSIONS: dict[str, Any] = {}

_AGENT_ID_ITEM_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

# 会話履歴（API 経由）の上限
_MAX_CONVERSATION_HISTORY_ITEMS = 40
_MAX_CONVERSATION_MESSAGE_CHARS = 120_000

# file_write の content を SSE に載せる上限（DevTools / UI 負荷対策）
_TOOL_SSE_MAX_CONTENT_CHARS = 8192


ChatMode = Literal["default", "skills", "orchestrate", "swarm", "workflow"]

_ORCH_SSE_META = {"phase": "orchestrate", "agent": "orchestrator"}
_TOOL_PHASE_AGENT: dict[str, tuple[str, str]] = {
    "consult_distill": ("specialist", "distill"),
    "consult_architecture": ("specialist", "architecture"),
    "consult_review": ("specialist", "review"),
}


def _tool_input_fingerprint(tool_input: Any) -> str:
    try:
        return json.dumps(tool_input, sort_keys=True, ensure_ascii=False, default=str)
    except TypeError:
        return repr(tool_input)


def _normalize_current_tool_use_for_sse(ctu: dict[str, Any]) -> dict[str, Any] | None:
    """Strands のストリームではツール入力が蓄積中は JSON 文字列（handle_content_block_delta）。
    完全なオブジェクトにパースできたときだけ返す（strands.event_loop.streaming の contentBlockStop 相当）。
    部分 JSON の段階では None を返し、SSE のノイズと誤解を防ぐ。
    """
    name = str(ctu.get("name") or "")
    if not name:
        return None
    inp = ctu.get("input")
    if isinstance(inp, dict):
        return ctu
    if isinstance(inp, str):
        s = inp.strip()
        if not s:
            return None
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        out = dict(ctu)
        out["input"] = parsed
        return out
    return None


def _sanitize_tool_input_for_sse(tool_name: str, tool_input: Any) -> Any:
    if tool_name == "file_write" and isinstance(tool_input, dict):
        out = dict(tool_input)
        c = out.get("content")
        if isinstance(c, str) and len(c) > _TOOL_SSE_MAX_CONTENT_CHARS:
            out["content"] = (
                c[:_TOOL_SSE_MAX_CONTENT_CHARS]
                + f"\n... (SSE 表示用に切り詰め: 全 {len(c)} 文字)"
            )
            out["_sse_content_truncated"] = True
        return out
    return tool_input


def _tool_payload(
    ctu: dict[str, Any],
    *,
    stream_revision: int | None = None,
) -> dict[str, Any]:
    name = str(ctu.get("name") or "")
    payload: dict[str, Any] = {"type": "tool", "name": name}
    tool_input = ctu.get("input")
    if tool_input is not None:
        payload["input"] = _sanitize_tool_input_for_sse(name, tool_input)
    if ctu.get("error") is not None:
        payload["error"] = ctu.get("error")
    if ctu.get("status") is not None:
        payload["status"] = ctu.get("status")
    if stream_revision is not None:
        payload["stream_revision"] = stream_revision
    return payload


class _ToolStreamState:
    __slots__ = ("name", "input_fingerprint", "revision")

    def __init__(self) -> None:
        self.name: str | None = None
        self.input_fingerprint: str | None = None
        self.revision: int = 0

    def reset(self) -> None:
        self.name = None
        self.input_fingerprint = None
        self.revision = 0

    def should_emit_and_bump(self, tool_name: str, fingerprint: str) -> bool:
        if not tool_name:
            return False
        if tool_name != self.name:
            self.name = tool_name
            self.input_fingerprint = fingerprint
            self.revision = 0
            return True
        if fingerprint != self.input_fingerprint:
            self.input_fingerprint = fingerprint
            self.revision += 1
            return True
        return False


def _sse_with_meta(
    mode: str,
    payload: dict[str, Any],
    *,
    tool_name: str | None = None,
    orch_tool_map: dict[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    if mode != "orchestrate":
        return payload
    out = dict(payload)
    if tool_name:
        if orch_tool_map and tool_name in orch_tool_map:
            ph, ag = orch_tool_map[tool_name]
            out["phase"] = ph
            out["agent"] = ag
        elif tool_name in _TOOL_PHASE_AGENT:
            ph, ag = _TOOL_PHASE_AGENT[tool_name]
            out["phase"] = ph
            out["agent"] = ag
        else:
            out.update(_ORCH_SSE_META)
    else:
        out.update(_ORCH_SSE_META)
    return out


def _sse_swarm(node_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["phase"] = "swarm"
    out["agent"] = node_id
    return out


def _swarm_inner_to_sse(
    inner: dict[str, Any],
    node_id: str,
    tool_stream_state: list[_ToolStreamState],
) -> list[dict[str, Any]]:
    if inner.get("init_event_loop"):
        return []
    if list(inner.keys()) == ["event"]:
        return []
    if inner.get("result"):
        return []
    if inner.get("data"):
        tool_stream_state[0].reset()
        return [_sse_swarm(node_id, {"type": "text", "content": inner["data"]})]
    rt = inner.get("reasoningText")
    if rt:
        return [_sse_swarm(node_id, {"type": "reasoning", "content": rt})]
    ctu = inner.get("current_tool_use")
    if isinstance(ctu, dict):
        ctu_eff = _normalize_current_tool_use_for_sse(ctu)
        if ctu_eff is None:
            return []
        name = str(ctu_eff.get("name") or "")
        fp = _tool_input_fingerprint(ctu_eff.get("input"))
        st = tool_stream_state[0]
        if st.should_emit_and_bump(name, fp):
            return [
                _sse_swarm(
                    node_id,
                    _tool_payload(ctu_eff, stream_revision=st.revision),
                )
            ]
    return []


class ConversationHistoryItem(BaseModel):
    """Strands の user / assistant メッセージに対応（content はプレーンテキスト）。"""

    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=200_000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    mode: ChatMode = "default"
    attachments: list[dict[str, Any]] | None = None
    project_id: str = Field(
        default="default",
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    agent_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    conversation_history: list[ConversationHistoryItem] | None = None


class ChatResumeRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    interrupt_responses: list[dict[str, Any]] = Field(default_factory=list)


class AgentsMultiChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    attachments: list[dict[str, Any]] | None = None
    project_id: str = Field(
        default="default",
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    agent_ids: list[str] = Field(..., min_length=2)
    conversation_history: list[ConversationHistoryItem] | None = None

    @field_validator("agent_ids")
    @classmethod
    def _normalize_agent_ids(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for x in v:
            aid = normalize_agent_id(x)
            if not aid:
                raise ValueError("agent_ids に空の要素があります")
            if len(aid) > 128 or not _AGENT_ID_ITEM_PATTERN.match(aid):
                raise ValueError(f"無効な agent_id: {x!r}")
            out.append(aid)
        if len(set(out)) != len(out):
            raise ValueError("agent_ids に重複があります")
        return out


def _augment_message_with_attachments(
    base_message: str, attachments: list[dict[str, Any]] | None
) -> str:
    if not attachments:
        return base_message

    lines: list[str] = []
    for a in attachments:
        kind = a.get("kind")
        filename = a.get("filename")
        url = a.get("url")
        if not kind or not filename:
            continue
        fn_lit = json.dumps(filename, ensure_ascii=False)
        if url:
            lines.append(
                f"- {kind}: {filename} (url: {url}, file_read: area=\"inbox\", relative_path={fn_lit})"
            )
        else:
            lines.append(
                f"- {kind}: {filename} (file_read: area=\"inbox\", relative_path={fn_lit})"
            )

    if not lines:
        return base_message

    attachments_block = "\n".join(lines)
    return format_attachments_instruction(
        base_message=base_message, attachments_block=attachments_block
    )


def _strands_initial_messages(
    items: list[ConversationHistoryItem] | None,
) -> list[dict[str, Any]] | None:
    if not items:
        return None
    tail = items[-_MAX_CONVERSATION_HISTORY_ITEMS:]
    out: list[dict[str, Any]] = []
    for it in tail:
        text = (it.content or "").strip()
        if not text:
            continue
        if len(text) > _MAX_CONVERSATION_MESSAGE_CHARS:
            text = (
                text[:_MAX_CONVERSATION_MESSAGE_CHARS]
                + "\n... (履歴が長いため切り詰めました)"
            )
        out.append({"role": it.role, "content": [{"text": text}]})
    return out or None


def _compose_user_message_for_chat(
    message: str,
    attachments: list[dict[str, Any]] | None,
    workspace_index_block: str,
) -> str:
    aug = _augment_message_with_attachments(message, attachments)
    if workspace_index_block:
        return f"{workspace_index_block}\n\n{aug}"
    return aug


async def _async_iter_swarm_sse(
    swarm: Any,
    request: Request,
    user_message: str,
) -> AsyncIterator[str]:
    swarm_tool_state: list[_ToolStreamState] = [_ToolStreamState()]
    try:
        async for ev in swarm.stream_async(user_message):
            if await request.is_disconnected():
                yield _sse_data(
                    _sse_error(
                        "接続が切断されました。",
                        code="cancelled",
                    )
                )
                return
            et = ev.get("type")
            if et == "multiagent_result" and "result" in ev:
                r = ev["result"]
                st = getattr(r, "status", None)
                yield _sse_data(
                    {
                        "type": "done",
                        "stop_reason": str(st) if st is not None else None,
                        "phase": "swarm",
                    }
                )
                continue

            if et == "multiagent_handoff":
                frm = ev.get("from_node_ids") or []
                to = ev.get("to_node_ids") or []
                primary = to[0] if to else None
                payload: dict[str, Any] = {
                    "type": "handoff",
                    "from_agents": list(frm),
                    "to_agents": list(to),
                    "phase": "swarm",
                }
                if ev.get("message") is not None:
                    payload["message"] = ev["message"]
                if primary is not None:
                    payload["agent"] = primary
                swarm_tool_state[0].reset()
                yield _sse_data(payload)
                continue

            if et == "multiagent_node_stream":
                node_id = str(ev.get("node_id") or "swarm")
                inner = ev.get("event")
                if not isinstance(inner, dict):
                    continue
                for chunk in _swarm_inner_to_sse(inner, node_id, swarm_tool_state):
                    yield _sse_data(chunk)
                continue
    except asyncio.CancelledError:
        logger.info("chat swarm stream cancelled")
        raise
    except Exception as e:
        logger.exception("swarm.stream_async failed")
        yield _sse_data(_sse_error(str(e)))


def _sse_data(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False, default=str)}\n\n"


def _sse_error(message: str, *, code: str = "execution") -> dict[str, Any]:
    return {"type": "error", "message": message, "code": code}


def _interrupts_payload(r: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    interrupts = getattr(r, "interrupts", None)
    if not interrupts:
        return out
    for it in interrupts:
        try:
            out.append(
                {
                    "id": getattr(it, "id", None),
                    "name": getattr(it, "name", None),
                    "reason": getattr(it, "reason", None),
                }
            )
        except Exception:
            continue
    return out


async def stream_chat(body: ChatRequest, request: Request) -> StreamingResponse:
    workspace = ensure_project_workspace(body.project_id)
    try:
        team_context, skills_root = resolve_skills_for_project(body.project_id)
    except ProjectMetaJsonError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if body.mode == "workflow" and not workflow_enabled(team_context):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "workflow_requires_developer",
                "message": "workflow は Developer 文脈のプロジェクトでのみ利用可能です。",
            },
        )

    if body.mode in ("skills", "orchestrate", "swarm") and not skills_root.is_dir():
        raise HTTPException(
            status_code=422,
            detail=f"Skills が見つかりません: {skills_root}",
        )
    if body.mode == "default" and not skills_root.is_dir():
        logger.warning("Skills 参照パスが存在しません: %s", skills_root)
    logger.info(
        "chat mode=%s project_id=%s workspace=%s team_context=%s skills_ref=%s",
        body.mode,
        body.project_id,
        workspace,
        team_context,
        skills_root,
    )

    workspace_index_block = ""
    if body.mode in ("skills", "orchestrate", "swarm"):
        workspace_index_block = format_workspace_index_block(workspace)
        log_workspace_index_debug(
            project_id=body.project_id,
            workspace=workspace,
            index_text=workspace_index_block,
        )

    user_message = _compose_user_message_for_chat(
        body.message, body.attachments, workspace_index_block
    )
    initial_messages = _strands_initial_messages(body.conversation_history)

    async def generate():
        if body.mode == "swarm":
            try:
                swarm = build_swarm(
                    workspace,
                    skills_root,
                    workspace_context_suffix=workspace_index_block,
                    coordinator_initial_messages=initial_messages,
                )
            except ValueError as e:
                yield _sse_data(_sse_error(str(e)))
                return

            async for line in _async_iter_swarm_sse(swarm, request, user_message):
                yield line
            return

        if body.mode == "workflow":
            if not body.agent_id:
                yield _sse_data(
                    _sse_error('workflow のとき agent_id は必須です', code="validation")
                )
                return
            try:
                from src.infrastructure.workflow_engine import run_workflow_sse

                async for line in run_workflow_sse(
                    workspace=workspace,
                    project_id=body.project_id,
                    workflow_id=body.agent_id,
                    attachments=body.attachments,
                    request=request,
                ):
                    yield line
            except ValueError as e:
                yield _sse_data(_sse_error(str(e), code="validation"))
            return

        orch_tool_map: dict[str, tuple[str, str]] | None = None
        if body.mode == "orchestrate" and body.agent_id:
            try:
                od = load_orchestrator_definition(workspace, body.agent_id)
                orch_tool_map = {
                    s.tool_name: ("specialist", s.name) for s in od.specialists
                }
            except ValueError:
                orch_tool_map = None

        if body.agent_id and body.mode not in ("skills", "orchestrate", "workflow"):
            yield _sse_data(
                _sse_error(
                    'agent_id は mode="skills" または mode="orchestrate" または mode="workflow" のときのみ指定できます',
                    code="validation",
                )
            )
            return

        try:
            agent = build_agent(
                mode=body.mode,
                workspace_root=workspace,
                skills_root=skills_root,
                agent_id=body.agent_id,
                specialist_query_prefix=workspace_index_block
                if body.mode == "orchestrate"
                else "",
                initial_messages=initial_messages,
            )
        except ValueError as e:
            yield _sse_data(
                _sse_with_meta(
                    body.mode, _sse_error(str(e)), orch_tool_map=orch_tool_map
                ),
            )
            return

        tool_stream = _ToolStreamState()
        try:
            async for ev in agent.stream_async(user_message):
                if await request.is_disconnected():
                    yield _sse_data(
                        _sse_with_meta(
                            body.mode,
                            _sse_error(
                                "接続が切断されました。",
                                code="cancelled",
                            ),
                            orch_tool_map=orch_tool_map,
                        )
                    )
                    return
                if "result" in ev:
                    r = ev["result"]
                    if str(getattr(r, "stop_reason", "")) == "interrupt":
                        session_id = uuid.uuid4().hex
                        _INTERRUPT_SESSIONS[session_id] = agent
                        yield _sse_data(
                            _sse_with_meta(
                                body.mode,
                                {
                                    "type": "interrupt",
                                    "session_id": session_id,
                                    "interrupts": _interrupts_payload(r),
                                },
                                orch_tool_map=orch_tool_map,
                            )
                        )
                        return
                    yield _sse_data(
                        _sse_with_meta(
                            body.mode,
                            {
                                "type": "done",
                                "stop_reason": str(r.stop_reason)
                                if r.stop_reason is not None
                                else None,
                            },
                            orch_tool_map=orch_tool_map,
                        )
                    )
                    continue

                if ev.get("init_event_loop"):
                    continue

                if list(ev.keys()) == ["event"]:
                    continue

                if ev.get("data"):
                    tool_stream.reset()
                    yield _sse_data(
                        _sse_with_meta(
                            body.mode,
                            {"type": "text", "content": ev["data"]},
                            orch_tool_map=orch_tool_map,
                        )
                    )
                    continue

                rt = ev.get("reasoningText")
                if rt:
                    yield _sse_data(
                        _sse_with_meta(
                            body.mode,
                            {"type": "reasoning", "content": rt},
                            orch_tool_map=orch_tool_map,
                        )
                    )
                    continue

                ctu = ev.get("current_tool_use")
                if isinstance(ctu, dict):
                    ctu_eff = _normalize_current_tool_use_for_sse(ctu)
                    if ctu_eff is None:
                        continue
                    name = str(ctu_eff.get("name") or "")
                    fp = _tool_input_fingerprint(ctu_eff.get("input"))
                    if tool_stream.should_emit_and_bump(name, fp):
                        logger.debug(
                            "chat sse tool name=%s stream_revision=%s fp_len=%s",
                            name,
                            tool_stream.revision,
                            len(fp),
                        )
                        yield _sse_data(
                            _sse_with_meta(
                                body.mode,
                                _tool_payload(
                                    ctu_eff, stream_revision=tool_stream.revision
                                ),
                                tool_name=name,
                                orch_tool_map=orch_tool_map,
                            )
                        )
        except asyncio.CancelledError:
            logger.info("chat agent stream cancelled")
            raise
        except Exception as e:
            logger.exception("agent.stream_async failed")
            yield _sse_data(
                _sse_with_meta(
                    body.mode, _sse_error(str(e)), orch_tool_map=orch_tool_map
                ),
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def stream_agents_multi_chat(
    body: AgentsMultiChatRequest, request: Request
) -> StreamingResponse:
    workspace = ensure_project_workspace(body.project_id)
    try:
        _tc, skills_root = resolve_skills_for_project(body.project_id)
    except ProjectMetaJsonError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if not skills_root.is_dir():
        raise HTTPException(
            status_code=422,
            detail=f"Skills が見つかりません: {skills_root}",
        )
    logger.info(
        "chat agents-multi project_id=%s workspace=%s agent_ids=%s skills_ref=%s",
        body.project_id,
        workspace,
        body.agent_ids,
        skills_root,
    )
    workspace_index_block = format_workspace_index_block(workspace)
    log_workspace_index_debug(
        project_id=body.project_id,
        workspace=workspace,
        index_text=workspace_index_block,
    )
    user_message = _compose_user_message_for_chat(
        body.message, body.attachments, workspace_index_block
    )
    initial_messages = _strands_initial_messages(body.conversation_history)

    async def generate():
        try:
            swarm = build_swarm_from_workspace_agent_ids(
                workspace,
                skills_root,
                body.agent_ids,
                workspace_context_suffix=workspace_index_block,
                coordinator_initial_messages=initial_messages,
            )
        except ValueError as e:
            yield _sse_data(_sse_error(str(e)))
            return
        async for line in _async_iter_swarm_sse(swarm, request, user_message):
            yield line

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def stream_chat_resume(body: ChatResumeRequest, request: Request) -> StreamingResponse:
    agent = _INTERRUPT_SESSIONS.get(body.session_id)
    if agent is None:
        raise HTTPException(status_code=422, detail="無効な session_id です")

    async def generate():
        tool_stream = _ToolStreamState()
        try:
            async for ev in agent.stream_async(body.interrupt_responses):
                if await request.is_disconnected():
                    yield _sse_data(
                        _sse_error(
                            "接続が切断されました。",
                            code="cancelled",
                        )
                    )
                    return
                if "result" in ev:
                    r = ev["result"]
                    if str(getattr(r, "stop_reason", "")) == "interrupt":
                        yield _sse_data(
                            {
                                "type": "interrupt",
                                "session_id": body.session_id,
                                "interrupts": _interrupts_payload(r),
                            }
                        )
                        return
                    _INTERRUPT_SESSIONS.pop(body.session_id, None)
                    yield _sse_data(
                        {
                            "type": "done",
                            "stop_reason": str(r.stop_reason)
                            if r.stop_reason is not None
                            else None,
                        }
                    )
                    return

                if ev.get("init_event_loop"):
                    continue
                if list(ev.keys()) == ["event"]:
                    continue
                if ev.get("data"):
                    tool_stream.reset()
                    yield _sse_data({"type": "text", "content": ev["data"]})
                    continue
                rt = ev.get("reasoningText")
                if rt:
                    yield _sse_data({"type": "reasoning", "content": rt})
                    continue
                ctu = ev.get("current_tool_use")
                if isinstance(ctu, dict):
                    ctu_eff = _normalize_current_tool_use_for_sse(ctu)
                    if ctu_eff is None:
                        continue
                    name = str(ctu_eff.get("name") or "")
                    fp = _tool_input_fingerprint(ctu_eff.get("input"))
                    if tool_stream.should_emit_and_bump(name, fp):
                        yield _sse_data(
                            _tool_payload(
                                ctu_eff, stream_revision=tool_stream.revision
                            )
                        )
        except asyncio.CancelledError:
            logger.info("chat resume stream cancelled")
            raise
        except Exception as e:
            logger.exception("agent.stream_async resume failed")
            yield _sse_data(_sse_error(str(e)))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

