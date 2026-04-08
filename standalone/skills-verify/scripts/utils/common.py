from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from strands import Agent
from strands.vended_plugins.skills import AgentSkills
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel
from strands_tools import file_read, file_write


FIXED_MAX_TOKENS = 8091
STATE_KEY = "agent_skills"


@dataclass(frozen=True)
class VerifyPaths:
    repo_root: Path
    verify_root: Path
    scripts_root: Path
    skills_root: Path
    results_root: Path
    testdata_root: Path
    skills_machine_root: Path


def resolve_paths() -> VerifyPaths:
    scripts_root = Path(__file__).resolve().parents[1]
    verify_root = scripts_root.parent
    repo_root = verify_root.parents[1]
    skills_root = repo_root / "KC-Dev-Agents-main" / ".agent" / "skills"
    return VerifyPaths(
        repo_root=repo_root,
        verify_root=verify_root,
        scripts_root=scripts_root,
        skills_root=skills_root,
        results_root=verify_root / "results",
        testdata_root=verify_root / "testdata",
        skills_machine_root=verify_root / "skills-machine",
    )


def ensure_prerequisites(paths: VerifyPaths) -> None:
    if not paths.skills_root.exists():
        raise RuntimeError(f"KC skills dir not found: {paths.skills_root}")

    required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "AWS_BEDROCK_MODEL_ID"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def load_environment() -> VerifyPaths:
    load_dotenv()
    paths = resolve_paths()
    ensure_prerequisites(paths)
    paths.results_root.mkdir(parents=True, exist_ok=True)
    return paths


def build_bedrock_model() -> BedrockModel:
    model_id = os.getenv("AWS_BEDROCK_MODEL_ID")
    if not model_id:
        raise RuntimeError("AWS_BEDROCK_MODEL_ID is not set in standalone/.env")

    temperature = float(os.getenv("TEMPERATURE", "0.0"))
    streaming = os.getenv("ENABLE_STREAMING", "True").lower() == "true"

    return BedrockModel(
        model_id=model_id,
        temperature=temperature,
        max_tokens=FIXED_MAX_TOKENS,
        streaming=streaming,
    )


def create_agent(paths: VerifyPaths, model: BedrockModel, include_file_write: bool = False) -> Agent:
    plugin = AgentSkills(skills=str(paths.skills_root), state_key=STATE_KEY)
    tools = [file_read]
    if include_file_write:
        tools.append(file_write)

    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
        per_turn=True,
    )
    return Agent(
        model=model,
        plugins=[plugin],
        tools=tools,
        conversation_manager=conversation_manager,
    )


def snapshot_state(agent: Agent, state_key: str = STATE_KEY) -> Any:
    try:
        st = getattr(agent, "state", None)
        if st is None:
            return None
        if hasattr(st, "get") and callable(getattr(st, "get")):
            return st.get(state_key)
        if isinstance(st, dict):
            return st.get(state_key)
        return str(st)
    except Exception as exc:
        return f"<failed to snapshot state: {exc}>"


def classify_exception(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "maxtokensreachedexception" in text or "max_tokens" in text:
        return "token"
    if "cp932" in text or "encoding" in text or "unicode" in text:
        return "encoding"
    if "tool" in text and ("failed" in text or "error" in text):
        return "tool"
    if "missing required environment variables" in text or "not set" in text:
        return "env"
    return "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_full_run_log_path(paths: VerifyPaths, mode: str) -> Path | None:
    enabled = env_bool("WORKFLOW_FULL_LOG_ENABLED", True)
    if not enabled or mode != "full":
        return None

    filename = os.getenv("WORKFLOW_FULL_LOG_FILENAME", "").strip()
    if not filename:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-UTC")
        filename = f"workflow-full-{timestamp}.log"
    return paths.results_root / filename


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def remove_reviewer_field(json_path: str) -> bool:
    """Remove reviewer field from decision log JSON if present."""
    path = Path(json_path)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict) or "reviewer" not in data:
        return False
    data.pop("reviewer", None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def build_artifact_paths(paths: VerifyPaths) -> dict[str, str]:
    review_id = datetime.now(timezone.utc).strftime("REV-%Y-%m-%d-%H%M%S-UTC")
    return {
        "doc_path": (paths.testdata_root / "doc.md").as_posix(),
        "sample_ts_path": (paths.testdata_root / "sample.ts").as_posix(),
        "notes_path": (paths.skills_machine_root / "20_notes" / "spec_distilled.md").as_posix(),
        "story_map_path": (paths.skills_machine_root / "20_notes" / "story_map.md").as_posix(),
        "proposal_path": (paths.skills_machine_root / "30_proposal" / "proposal.md").as_posix(),
        "architecture_path": (paths.skills_machine_root / "30_proposal" / "architecture.md").as_posix(),
        "diagram_path": (paths.skills_machine_root / "30_proposal" / "architecture_diagram.md").as_posix(),
        "ts_review_path": (paths.skills_machine_root / "30_proposal" / "ts_review.md").as_posix(),
        "py_review_path": (paths.skills_machine_root / "30_proposal" / "py_review.md").as_posix(),
        "test_plan_path": (paths.skills_machine_root / "30_proposal" / "test_plan.md").as_posix(),
        "subagent_design_path": (paths.skills_machine_root / "30_proposal" / "subagent_design.md").as_posix(),
        "new_skill_spec_path": (paths.skills_machine_root / "30_proposal" / "new_skill_spec.md").as_posix(),
        "adr_path": (
            paths.skills_machine_root / "40_decision_log" / f"ADR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-UTC')}.md"
        ).as_posix(),
        "decision_path": (paths.skills_machine_root / "40_decision_log" / f"{review_id}.json").as_posix(),
        "validation_report_path": (paths.skills_machine_root / "40_decision_log" / "validation_report.json").as_posix(),
        "review_example_path": (
            paths.skills_root / "review" / "references" / "technical-review-examples.md"
        ).resolve().as_posix(),
        "review_id": review_id,
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
    }


def build_rerun_decision_path(paths: VerifyPaths) -> str:
    rerun_id = datetime.now(timezone.utc).strftime("REV-RERUN-%Y-%m-%d-%H%M%S-UTC")
    return (paths.skills_machine_root / "40_decision_log" / f"{rerun_id}.json").as_posix()


def extract_text(result_obj: Any) -> str:
    if result_obj is None:
        return ""
    result = getattr(result_obj, "result", None)
    if result is None:
        return str(result_obj)
    message = getattr(result, "message", None)
    if not message:
        return str(result)
    content = message.get("content", [])
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return str(first.get("text", ""))
    return str(result)

