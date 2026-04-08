from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

_TOOL_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
_SKILL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

logger = logging.getLogger(__name__)


AgentKind = Literal["single", "orchestrator", "swarm"]

_ALLOWED_TOOL_CANDIDATES: set[str] = {
    "file_read",
    "file_write",
    "workspace_list",
    "pdf_convert_to_inbox",
    "diagram_generate_drawio",
    "web_fetch_text",
    "brave_web_search",
}


@dataclass(frozen=True)
class AgentDefinitionMeta:
    agent_id: str
    name: str
    kind: AgentKind
    description: str
    source_path: Path
    department: str
    division: str
    icon_key: str


@dataclass(frozen=True)
class AgentDefinition(AgentDefinitionMeta):
    system_prompt: str
    allowed_tools: tuple[str, ...]
    skills: tuple[str, ...]


@dataclass(frozen=True)
class SpecialistSpec:
    tool_name: str
    name: str
    role_instructions: str


@dataclass(frozen=True)
class OrchestratorDefinition(AgentDefinitionMeta):
    system_prompt: str
    allowed_tools: tuple[str, ...]
    skills: tuple[str, ...]
    specialists: tuple[SpecialistSpec, ...]


def normalize_agent_id(agent_id: str) -> str:
    return (agent_id or "").strip().lower()


def agents_dir(workspace_root: Path) -> Path:
    return (workspace_root.resolve() / "agents").resolve()


def _find_definition_path(workspace_root: Path, agent_id: str) -> Path | None:
    aid = normalize_agent_id(agent_id)
    if not aid:
        return None
    d = agents_dir(workspace_root)
    yml = d / f"{aid}.yml"
    yaml_path = d / f"{aid}.yaml"
    if yaml_path.is_file():
        return yaml_path
    if yml.is_file():
        return yml
    return None


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return str(v)


def _as_list_of_str(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: list[str] = []
        for x in v:
            s = _as_str(x).strip()
            if s:
                out.append(s)
        return out
    if isinstance(v, str):
        s = v.strip()
        return [s] if s else []
    return []


def _parse_allowed_tools(data: dict[str, Any], *, label: str) -> tuple[str, ...]:
    allowed_tools_raw = [s.strip() for s in _as_list_of_str(data.get("allowed_tools")) if s.strip()]
    if not allowed_tools_raw:
        raise ValueError(f"allowed_tools は必須です ({label})")

    normalized: list[str] = []
    unknown: list[str] = []
    for t in allowed_tools_raw:
        tn = t.strip()
        if tn not in _ALLOWED_TOOL_CANDIDATES:
            unknown.append(tn)
            continue
        if tn not in normalized:
            normalized.append(tn)
    if unknown:
        raise ValueError(
            f"unknown tools in allowed_tools: {', '.join(unknown)} ({label})"
        )
    if "file_read" not in normalized:
        raise ValueError(f"{label}: allowed_tools に file_read を含めてください")

    return tuple(normalized)


def _parse_department_division_icon(data: dict[str, Any]) -> tuple[str, str, str]:
    department = _as_str(data.get("department")).strip()
    division = _as_str(data.get("division")).strip()
    icon_key = _as_str(data.get("icon_key")).strip()
    return department, division, icon_key


def _parse_skills(data: dict[str, Any], *, label: str) -> tuple[str, ...]:
    """
    YAML の `skills` と `allowed_skills`（互換）を統合して返す。
    """
    raw = _as_list_of_str(data.get("skills"))
    compat = _as_list_of_str(data.get("allowed_skills"))
    merged = raw + compat
    if not merged:
        return ()
    out: list[str] = []
    invalid: list[str] = []
    for s in merged:
        name = s.strip()
        if not name:
            continue
        if not _SKILL_NAME_PATTERN.fullmatch(name):
            invalid.append(name)
            continue
        if name not in out:
            out.append(name)
    if invalid:
        raise ValueError(f"{label}: skills/allowed_skills に不正な識別子があります: {', '.join(invalid)}")
    return tuple(out)


def _read_agent_yaml_text(path: Path) -> str:
    """UTF-8 を優先。失敗時は cp932 / cp1252 を試す（旧 strands_tools 書き込みの救済用）。"""
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    for enc in ("cp932", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _load_yaml_dict(workspace_root: Path, agent_id: str) -> tuple[Path, dict[str, Any], str]:
    p = _find_definition_path(workspace_root, agent_id)
    if p is None:
        raise ValueError(f"agent 定義が見つかりません: {agent_id}")

    raw = _read_agent_yaml_text(p)
    data = yaml.safe_load(raw) or {}
    expected_id = normalize_agent_id(agent_id)
    if not isinstance(data, dict):
        raise ValueError(
            f"agent 定義の形式が不正です（agent_id={expected_id}、YAMLのトップレベルは map を想定）"
        )

    defined_id = normalize_agent_id(_as_str(data.get("id")))
    if defined_id and defined_id != expected_id:
        raise ValueError(f"agent id が一致しません: agent_id={expected_id} got={defined_id}")

    return p, data, expected_id


def load_single_agent_definition(workspace_root: Path, agent_id: str) -> AgentDefinition:
    p, data, expected_id = _load_yaml_dict(workspace_root, agent_id)

    kind = _as_str(data.get("kind") or "single").strip().lower()
    if kind not in ("single", "orchestrator", "swarm"):
        raise ValueError(f"kind が不正です: {kind} (agent_id={expected_id})")
    if kind != "single":
        raise ValueError(
            f"mode=skills + agent_id では kind=single の YAML が必要です (agent_id={expected_id})"
        )

    display_name = _as_str(data.get("name")).strip()
    if not display_name:
        raise ValueError(f"name は必須です (agent_id={expected_id})")

    description = _as_str(data.get("description")).strip()
    system_prompt = _as_str(data.get("system_prompt")).strip()
    if not system_prompt:
        raise ValueError(f"system_prompt は必須です (agent_id={expected_id})")

    label = f"single agent (agent_id={expected_id})"
    allowed_tools = _parse_allowed_tools(data, label=label)
    skills = _parse_skills(data, label=label)
    if len(skills) > 1:
        raise ValueError(
            f"1 スキル = 1 エージェントのため、skills は高々 1 件にしてください "
            f"(agent_id={expected_id}, 指定数={len(skills)})"
        )
    department, division, icon_key = _parse_department_division_icon(data)

    return AgentDefinition(
        agent_id=expected_id,
        name=display_name,
        kind="single",
        description=description,
        source_path=p,
        department=department,
        division=division,
        icon_key=icon_key,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        skills=skills,
    )


def load_agent_definition(workspace_root: Path, agent_id: str) -> AgentDefinition:
    return load_single_agent_definition(workspace_root, agent_id)


def load_orchestrator_definition(workspace_root: Path, agent_id: str) -> OrchestratorDefinition:
    p, data, expected_id = _load_yaml_dict(workspace_root, agent_id)

    kind = _as_str(data.get("kind") or "single").strip().lower()
    if kind != "orchestrator":
        raise ValueError(
            f"mode=orchestrate + agent_id では kind=orchestrator の YAML が必要です (agent_id={expected_id})"
        )

    display_name = _as_str(data.get("name")).strip()
    if not display_name:
        raise ValueError(f"name は必須です (agent_id={expected_id})")

    description = _as_str(data.get("description")).strip()
    system_prompt = _as_str(data.get("system_prompt")).strip()
    if not system_prompt:
        raise ValueError(f"system_prompt は必須です (agent_id={expected_id})")

    orch_label = f"orchestrator (agent_id={expected_id})"
    allowed_tools = _parse_allowed_tools(data, label=orch_label)
    skills = _parse_skills(data, label=orch_label)

    raw_specs = data.get("specialists")
    if not isinstance(raw_specs, list) or len(raw_specs) == 0:
        raise ValueError(f"specialists は1件以上の配列が必須です (agent_id={expected_id})")

    specs: list[SpecialistSpec] = []
    seen_tools: set[str] = set()
    for i, item in enumerate(raw_specs):
        if not isinstance(item, dict):
            raise ValueError(
                f"specialists[{i}] は map である必要があります (agent_id={expected_id})"
            )
        tool_name = _as_str(item.get("tool_name")).strip()
        if not tool_name or not _TOOL_NAME_PATTERN.fullmatch(tool_name):
            raise ValueError(
                f"specialists[{i}].tool_name は ^[a-z_][a-z0-9_]*$ 形式の識別子にしてください (agent_id={expected_id})"
            )
        if tool_name in seen_tools:
            raise ValueError(
                f"specialists の tool_name が重複しています: {tool_name} (agent_id={expected_id})"
            )
        seen_tools.add(tool_name)
        sp_name = _as_str(item.get("name")).strip()
        if not sp_name:
            raise ValueError(f"specialists[{i}].name は必須です (agent_id={expected_id})")
        role = _as_str(item.get("role_instructions")).strip()
        if not role:
            raise ValueError(
                f"specialists[{i}].role_instructions は必須です (agent_id={expected_id})"
            )
        specs.append(
            SpecialistSpec(
                tool_name=tool_name,
                name=sp_name,
                role_instructions=role,
            )
        )

    department, division, icon_key = _parse_department_division_icon(data)

    return OrchestratorDefinition(
        agent_id=expected_id,
        name=display_name,
        kind="orchestrator",
        description=description,
        source_path=p,
        department=department,
        division=division,
        icon_key=icon_key,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        skills=skills,
        specialists=tuple(specs),
    )


def list_agent_definitions(workspace_root: Path) -> list[AgentDefinitionMeta]:
    d = agents_dir(workspace_root)
    if not d.is_dir():
        return []

    metas: list[AgentDefinitionMeta] = []
    candidates = sorted(list(d.glob("*.yaml")) + list(d.glob("*.yml")), key=lambda p: p.name)
    for p in candidates:
        if not p.is_file():
            continue
        agent_id = normalize_agent_id(p.stem)
        if not agent_id:
            continue
        try:
            raw = _read_agent_yaml_text(p)
            data = yaml.safe_load(raw) or {}
            if not isinstance(data, dict):
                continue
            kind = _as_str(data.get("kind") or "single").strip().lower()
            if kind not in ("single", "orchestrator", "swarm"):
                kind = "single"
            name = _as_str(data.get("name")).strip() or agent_id
            description = _as_str(data.get("description")).strip()
            department, division, icon_key = _parse_department_division_icon(data)
            metas.append(
                AgentDefinitionMeta(
                    agent_id=agent_id,
                    name=name,
                    kind=kind,  # type: ignore[arg-type]
                    description=description,
                    source_path=p,
                    department=department,
                    division=division,
                    icon_key=icon_key,
                )
            )
        except OSError as e:
            logger.warning("agent YAML を読めません: %s (%s)", p, e)
            continue
        except Exception as e:
            logger.warning("agent YAML の解析に失敗しました: %s (%s)", p, e)
            continue
    return metas

