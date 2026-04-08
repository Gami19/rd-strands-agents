from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Request

from src.infrastructure.team_context import resolve_workflows_root
from src.infrastructure.compat_tools import SUPPORTED_DOC_EXTS


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse_data(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False, default=str)}\n\n"


def _sse_error(message: str, *, code: str = "execution") -> dict[str, Any]:
    return {"type": "error", "message": message, "code": code, "phase": "workflow"}


def _normalize_filename(filename: str) -> str:
    # ../ などのパス混入を避ける（attachments 側も安全化されている前提だが念のため）。
    return Path(filename).name


def _wf_stage1_filename(workflow_id: str, run_id: str) -> str:
    return f"wf__{workflow_id}__{run_id}__phase1__stage1.md"


def _wf_memo_filename(workflow_id: str, run_id: str) -> str:
    return f"wf__{workflow_id}__{run_id}__phase3__memo.md"


def _wf_state_filename(workflow_id: str, run_id: str) -> str:
    return f"wf__{workflow_id}__{run_id}__state.json"


def _wf_recovery_filename(workflow_id: str, run_id: str) -> str:
    return f"wf__{workflow_id}__{run_id}__recovery.json"


def _select_single_input_attachment(
    attachments: list[dict[str, Any]] | None,
) -> tuple[str, str]:
    if not attachments:
        raise ValueError("attachments が空です（workflow は入力ファイルが必要です）")

    candidates: list[dict[str, Any]] = []
    for a in attachments:
        filename = a.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            continue
        fn = Path(filename).name
        if Path(fn).suffix.lower() in SUPPORTED_DOC_EXTS:
            candidates.append(a)

    if len(candidates) != 1:
        names = [
            str(Path(a.get("filename", "")).name)
            for a in candidates
            if isinstance(a, dict) and isinstance(a.get("filename"), str)
        ]
        raise ValueError(f"対応拡張子の添付が 1 件になる必要があります: {names}")

    a0 = candidates[0]
    filename = str(a0.get("filename"))
    kind = str(a0.get("kind") or "")
    return _normalize_filename(filename), kind


def _gate_stage1_basic(stage1_path: Path) -> tuple[bool, list[str]]:
    if not stage1_path.is_file():
        return False, ["stage1_missing"]
    try:
        size = stage1_path.stat().st_size
    except OSError:
        return False, ["stage1_stat_failed"]
    if size <= 0:
        return False, ["stage1_empty"]
    return True, []


_HEADING_RE = re.compile(r"^(#{1,6})\s+\S+", re.MULTILINE)
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$", re.MULTILINE)


def _gate_stage1_heuristics(stage1_text: str) -> tuple[bool, list[str], dict[str, Any]]:
    """
    MVP 用の簡易判定。
    - 見出しが一定数以上
    - テーブルっぽい区切り（--- セパレータ）が存在、またはパイプ行が多い
    - 文字化け記号が閾値以下
    """
    failure_codes: list[str] = []

    headings = len(_HEADING_RE.findall(stage1_text))
    if headings < 2:
        failure_codes.append("heading_insufficient")

    sep_lines = len(_TABLE_SEP_RE.findall(stage1_text))
    pipe_lines = sum(1 for line in stage1_text.splitlines() if "|" in line)
    table_like = (sep_lines >= 1) or (pipe_lines >= 5)
    if not table_like:
        failure_codes.append("missing_table_markers")

    mojibake_count = stage1_text.count("�") + stage1_text.count("□")
    if mojibake_count > 2:
        failure_codes.append("mojibake_detected")

    metrics: dict[str, Any] = {
        "headings": headings,
        "sep_lines": sep_lines,
        "pipe_lines": pipe_lines,
        "mojibake_count": mojibake_count,
    }
    return (len(failure_codes) == 0), failure_codes, metrics


def _convert_with_docling(input_path: Path, output_path: Path, *, ocr: bool) -> None:
    # ocr は MVP では利用されない（compat_tools 側も未接続）。
    _ = ocr
    try:
        from docling.document_converter import DocumentConverter
    except ModuleNotFoundError as e:
        raise RuntimeError("docling is not installed") from e

    converter = DocumentConverter()
    result = converter.convert(str(input_path))
    markdown = result.document.export_to_markdown()
    frontmatter = (
        "---\n"
        f'source: "{input_path.name}"\n'
        f'converted_at: "{_utc_now_iso()}"\n'
        'converter: "docling"\n'
        "---\n\n"
    )
    output_path.write_text(frontmatter + markdown, encoding="utf-8")


async def run_workflow_sse(
    *,
    workspace: Path,
    project_id: str,
    workflow_id: str,
    attachments: list[dict[str, Any]] | None,
    request: Request,
    max_attempts: int = 2,
) -> AsyncIterator[str]:
    """
    MVP: 3 workflow を共通エンジンで再現する。
    - Phase1: 添付を docling で inbox に変換（stage1 上書き固定名）
    - Phase2: stage1 に対して簡易Gate
    - 失敗時: Phase1 を attempt 最大2回
    - recovery/state/memo を inbox にフラット保存
    """
    run_id = uuid.uuid4().hex
    inbox = (workspace / "inbox").resolve()

    wf_root = resolve_workflows_root()
    if not wf_root.is_dir():
        raise ValueError(f"workflows ルートが存在しません: {wf_root}")

    workflow_md = (wf_root / f"{workflow_id}.md").resolve()
    if not workflow_md.is_file():
        raise ValueError(f"workflow md が見つかりません: {workflow_md}")

    input_filename, _kind = _select_single_input_attachment(attachments)
    input_path = (inbox / input_filename).resolve()
    if not input_path.is_file():
        raise ValueError(f"入力ファイルが inbox に存在しません: {input_path.name}")

    stage1_name = _wf_stage1_filename(workflow_id, run_id)
    stage1_path = (inbox / stage1_name).resolve()

    memo_name = _wf_memo_filename(workflow_id, run_id)
    memo_path = (inbox / memo_name).resolve()

    state_name = _wf_state_filename(workflow_id, run_id)
    state_path = (inbox / state_name).resolve()

    recovery_name = _wf_recovery_filename(workflow_id, run_id)
    recovery_path = (inbox / recovery_name).resolve()

    yield _sse_data(
        {
            "type": "text",
            "content": f"workflow start workflow_id={workflow_id} run_id={run_id}",
            "phase": "workflow",
            "agent": "workflow_engine",
        }
    )

    attempt = 1
    last_failure_codes: list[str] = []
    last_gate_metrics: dict[str, Any] = {}
    passed = False

    while attempt <= max_attempts:
        if await request.is_disconnected():
            return

        yield _sse_data(
            {
                "type": "text",
                "content": f"phase1 start attempt={attempt}",
                "phase": "workflow",
                "agent": "workflow_engine",
            }
        )

        try:
            _convert_with_docling(input_path, stage1_path, ocr=False)
        except RuntimeError as e:
            recovery = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "failed_stage": "phase1",
                "error": str(e),
                "attempt": attempt,
                "failure_codes": ["docling_missing"],
                "next_phase_after_failure": "phase1",
            }
            recovery_path.write_text(json.dumps(recovery, ensure_ascii=False, indent=2), encoding="utf-8")
            state = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "phase": "phase1",
                "pass": False,
                "attempt": attempt,
                "gate_last_result": None,
                "failure_codes": ["docling_missing"],
                "completed_at": _utc_now_iso(),
            }
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            memo_path.write_text(
                f"# Workflow Memo\nworkflow_id: {workflow_id}\nrun_id: {run_id}\ninput_filename: {input_filename}\n"
                f"phase: phase1\npass: false\nattempt: {attempt}\nfailure: docling_missing\n",
                encoding="utf-8",
            )
            yield _sse_data(_sse_error(f"workflow failed: docling error: {e}", code="workflow_docling"))
            return
        except Exception as e:
            last_failure_codes = ["docling_convert_failed"]
            last_gate_metrics = {"error": str(e)}
            # phase2 へ進まないので recovery/state を書いて終了（最短化優先）。
            recovery = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "failed_stage": "phase1",
                "error": str(e),
                "attempt": attempt,
                "failure_codes": last_failure_codes,
                "next_phase_after_failure": "phase1",
            }
            recovery_path.write_text(json.dumps(recovery, ensure_ascii=False, indent=2), encoding="utf-8")
            state = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "phase": "phase1",
                "pass": False,
                "attempt": attempt,
                "gate_last_result": None,
                "failure_codes": last_failure_codes,
                "completed_at": _utc_now_iso(),
            }
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            memo_path.write_text(
                f"# Workflow Memo\nworkflow_id: {workflow_id}\nrun_id: {run_id}\ninput_filename: {input_filename}\n"
                f"phase: phase1\npass: false\nattempt: {attempt}\nfailure: docling_convert_failed\n",
                encoding="utf-8",
            )
            yield _sse_data(_sse_error(f"workflow failed: {e}", code="workflow_phase1_error"))
            return

        stage1_ok, stage1_failure_codes = _gate_stage1_basic(stage1_path)
        if not stage1_ok:
            last_failure_codes = stage1_failure_codes
        else:
            stage1_text = stage1_path.read_text(encoding="utf-8", errors="replace")
            gate_pass, failure_codes, metrics = _gate_stage1_heuristics(stage1_text)
            last_failure_codes = failure_codes
            last_gate_metrics = metrics
            passed = gate_pass

        if passed:
            break

        yield _sse_data(
            {
                "type": "text",
                "content": f"phase2 gate failed attempt={attempt} failure_codes={last_failure_codes}",
                "phase": "workflow",
                "agent": "workflow_engine",
            }
        )

        attempt += 1

    # memo/state/recovery
    if passed:
        gate_last_result = {
            "pass": True,
            "failure_codes": [],
            "metrics": last_gate_metrics,
        }
        memo_path.write_text(
            "# Workflow Memo\n"
            f"workflow_id: {workflow_id}\n"
            f"run_id: {run_id}\n"
            f"input_filename: {input_filename}\n"
            f"stage1_filename: {stage1_name}\n"
            f"pass: true\n"
            f"attempt: {attempt}\n"
            f"gate_last_result: {json.dumps(gate_last_result, ensure_ascii=False)}\n",
            encoding="utf-8",
        )
        state_path.write_text(
            json.dumps(
                {
                    "workflow_id": workflow_id,
                    "run_id": run_id,
                    "project_id": project_id,
                    "input_filename": input_filename,
                    "phase": "phase3",
                    "pass": True,
                    "attempt": attempt,
                    "gate_last_result": gate_last_result,
                    "completed_at": _utc_now_iso(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        yield _sse_data(
            {
                "type": "text",
                "content": f"workflow done pass run_id={run_id}",
                "phase": "workflow",
                "agent": "workflow_engine",
            }
        )
        yield _sse_data({"type": "done", "stop_reason": "workflow_completed", "phase": "workflow"})
        return

    # failure path
    recovery_path.write_text(
        json.dumps(
            {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "failed_stage": "phase2",
                "attempts_executed": attempt - 1,
                "failure_codes": last_failure_codes,
                "gate_last_result": {
                    "pass": False,
                    "failure_codes": last_failure_codes,
                    "metrics": last_gate_metrics,
                },
                "next_phase_after_failure": "phase1",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(
            {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "project_id": project_id,
                "input_filename": input_filename,
                "phase": "phase2",
                "pass": False,
                "attempt": attempt - 1,
                "gate_last_result": {
                    "pass": False,
                    "failure_codes": last_failure_codes,
                    "metrics": last_gate_metrics,
                },
                "completed_at": _utc_now_iso(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    memo_path.write_text(
        "# Workflow Memo\n"
        f"workflow_id: {workflow_id}\n"
        f"run_id: {run_id}\n"
        f"input_filename: {input_filename}\n"
        f"stage1_filename: {stage1_name}\n"
        f"pass: false\n"
        f"attempt: {attempt - 1}\n"
        f"failure_codes: {json.dumps(last_failure_codes, ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    yield _sse_data(
        _sse_error(
            f"workflow failed: gate failed failure_codes={last_failure_codes}",
            code="workflow_gate_failed",
        )
    )
    return

