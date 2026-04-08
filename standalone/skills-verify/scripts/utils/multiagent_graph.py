from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strands.multiagent import GraphBuilder

from utils.common import (
    VerifyPaths,
    build_artifact_paths,
    build_rerun_decision_path,
    classify_exception,
    create_agent,
    extract_text,
    remove_reviewer_field,
    utc_now_iso,
)


@dataclass
class WorkflowRunResult:
    status: str
    summary: dict[str, Any]
    graph_results: dict[str, Any]


def _read_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _count_markdown_bullets(text: str) -> int:
    count = 0
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("- ") or s.startswith("* "):
            count += 1
    return count


def _check_distill_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    required_keywords = ["要件", "矛盾", "前提", "未確定"]
    missing = [kw for kw in required_keywords if kw not in text]
    if missing:
        reasons.append(f"必須セクション不足: {', '.join(missing)}")
    bullet_count = _count_markdown_bullets(text)
    if bullet_count < 5:
        reasons.append(f"箇条書き不足: {bullet_count} < 5")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"char_count": len(text), "bullet_count": bullet_count},
    }


def _check_proposal_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    section_count = sum(1 for line in text.splitlines() if line.lstrip().startswith("## "))
    if section_count == 0:
        reasons.append("章見出し不足: '## ' セクションなし")
    if section_count > 6:
        reasons.append(f"章数超過: {section_count} > 6")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    if len(text) > 4000:
        reasons.append(f"文字数超過: {len(text)} > 4000")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"char_count": len(text), "section_count_h2": section_count},
    }


def _count_mermaid_nodes(text: str) -> int:
    in_mermaid = False
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            if not in_mermaid and "mermaid" in s:
                in_mermaid = True
                continue
            if in_mermaid:
                in_mermaid = False
                continue
        if not in_mermaid:
            continue
        if "-->" in s:
            count += s.count("-->")
    return count + 1 if count > 0 else 0


def _check_story_map_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    has_activity = "活動" in text
    has_epic = "エピック" in text
    has_story = "ストーリー" in text
    if not (has_activity and has_epic and has_story):
        reasons.append("階層不足: 活動/エピック/ストーリー の3層未充足")

    priority_count = 0
    for token in ["高", "中", "低", "high", "medium", "low", "優先度"]:
        priority_count += text.lower().count(token.lower())
    if priority_count < 3:
        reasons.append(f"優先順明示不足: {priority_count} < 3")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"char_count": len(text), "priority_marker_count": priority_count},
    }


def _check_architecture_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    alternative_markers = ["代替案", "案1", "案2", "option"]
    alternative_score = sum(text.lower().count(m.lower()) for m in alternative_markers)
    if alternative_score < 2:
        reasons.append("代替案比較不足: 2案以上の比較が確認できない")
    if "採用理由" not in text and "理由" not in text:
        reasons.append("採用理由不足")

    nfr_tokens = ["性能", "可用性", "保守性", "セキュリティ"]
    nfr_hit = sum(1 for t in nfr_tokens if t in text)
    if nfr_hit < 3:
        reasons.append(f"非機能要件不足: {nfr_hit} < 3")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"char_count": len(text), "nfr_hit": nfr_hit, "alternative_score": alternative_score},
    }


def _check_decision_framework_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    required = ["決定", "根拠", "トレードオフ", "リスク"]
    missing = [k for k in required if k not in text]
    if missing:
        reasons.append(f"ADR必須項目不足: {', '.join(missing)}")
    if "ADR-" not in text and "ID" not in text and "識別子" not in text:
        reasons.append("追跡可能性不足: ID/識別子がない")
    if "UTC" not in text and "date" not in text.lower() and "日付" not in text:
        reasons.append("追跡可能性不足: 日付がない")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {"pass": len(reasons) == 0, "reasons": reasons, "metrics": {"char_count": len(text), "missing": missing}}


def _check_diagram_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    has_mermaid = "```mermaid" in text
    has_graph = "graph " in text or "flowchart " in text
    if not (has_mermaid and has_graph):
        reasons.append("図構文不足: mermaid + graph/flowchart が必要")
    node_count = _count_mermaid_nodes(text)
    if node_count < 3:
        reasons.append(f"図ノード不足: {node_count} < 3")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"node_count": node_count, "has_mermaid": has_mermaid, "has_graph": has_graph},
    }


def _check_effective_ts_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    issue_tokens = ["any", "unsafe", "assert", "型", "union"]
    issue_score = sum(text.lower().count(t.lower()) for t in issue_tokens)
    if issue_score < 3:
        reasons.append(f"型安全指摘不足: {issue_score} < 3")
    fix_tokens = ["修正案", "before", "after", "代替型"]
    fix_score = sum(text.lower().count(t.lower()) for t in fix_tokens)
    if fix_score < 1:
        reasons.append("修正提案不足")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {"pass": len(reasons) == 0, "reasons": reasons, "metrics": {"issue_score": issue_score, "fix_score": fix_score}}


def _check_robust_python_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    topics = ["例外", "型", "副作用", "I/O", "io境界", "i-o境界"]
    topic_hit = sum(1 for t in topics if t.lower() in text.lower())
    if topic_hit < 3:
        reasons.append(f"堅牢性指摘不足: {topic_hit} < 3")
    has_code = "```python" in text or "def " in text or "try:" in text
    if not has_code:
        reasons.append("実装可能性不足: 具体コード片がない")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {"pass": len(reasons) == 0, "reasons": reasons, "metrics": {"topic_hit": topic_hit, "has_code": has_code}}


def _check_test_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    required = ["正常", "異常", "境界"]
    missing = [k for k in required if k not in text]
    if missing:
        reasons.append(f"テスト分類不足: {', '.join(missing)}")
    test_case_count = _count_markdown_bullets(text)
    if test_case_count < 6:
        reasons.append(f"テストケース不足: {test_case_count} < 6")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"case_count": test_case_count, "char_count": len(text)},
    }


def _check_data_validation_quality(path: str) -> dict[str, Any]:
    reasons: list[str] = []
    obj = _load_json(path)
    if obj is None:
        return {"pass": False, "reasons": ["JSON読込失敗"], "metrics": {"required_keys_present": 0}}
    required = ["passed", "failed", "errors"]
    missing = [k for k in required if k not in obj]
    if missing:
        reasons.append(f"必須キー不足: {', '.join(missing)}")
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"required_keys_present": len(required) - len(missing)},
    }


def _check_agent_craft_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    role_markers = ["agent", "エージェント", "責務"]
    role_score = sum(text.lower().count(t.lower()) for t in role_markers)
    if role_score < 2:
        reasons.append("責務分離不足: エージェント責務が2つ以上確認できない")
    contract_keys = ["入力", "出力", "禁止事項"]
    missing = [k for k in contract_keys if k not in text]
    if missing:
        reasons.append(f"契約定義不足: {', '.join(missing)}")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {"pass": len(reasons) == 0, "reasons": reasons, "metrics": {"role_score": role_score, "missing": missing}}


def _check_skill_forge_quality(path: str) -> dict[str, Any]:
    text = _read_text(path)
    reasons: list[str] = []
    required = ["name", "use when", "tools", "inputs", "outputs"]
    missing = [k for k in required if k not in text.lower()]
    if missing:
        reasons.append(f"スキル定義不足: {', '.join(missing)}")
    step_markers = ["1.", "2.", "3.", "- "]
    step_score = sum(text.count(m) for m in step_markers)
    if step_score < 3:
        reasons.append(f"再利用手順不足: {step_score} < 3")
    if len(text) < 300:
        reasons.append(f"文字数不足: {len(text)} < 300")
    return {"pass": len(reasons) == 0, "reasons": reasons, "metrics": {"missing": missing, "step_score": step_score}}


def _load_json(path: str) -> dict[str, Any] | None:
    text = _read_text(path)
    if not text:
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def _has_high_priority_finding(findings: Any) -> bool:
    if isinstance(findings, list):
        for item in findings:
            if isinstance(item, dict):
                raw = " ".join(
                    [
                        str(item.get("severity", "")),
                        str(item.get("priority", "")),
                        str(item.get("level", "")),
                        str(item.get("title", "")),
                        str(item.get("text", "")),
                    ]
                ).lower()
            else:
                raw = str(item).lower()
            if any(token in raw for token in ["high", "critical", "重大", "高"]):
                return True
    return False


def _check_review_quality(path: str) -> dict[str, Any]:
    reasons: list[str] = []
    obj = _load_json(path)
    if obj is None:
        reasons.append("JSON読込失敗")
        return {"pass": False, "reasons": reasons, "metrics": {"required_keys_present": 0}}

    required_keys = ["review_id", "date_utc", "summary", "findings", "recommendations"]
    missing = [k for k in required_keys if k not in obj]
    if missing:
        reasons.append(f"必須キー不足: {', '.join(missing)}")

    findings = obj.get("findings", [])
    if not _has_high_priority_finding(findings):
        reasons.append("高優先度指摘不足")

    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {
            "required_keys_present": len(required_keys) - len(missing),
            "has_high_priority_finding": _has_high_priority_finding(findings),
        },
    }


def _node_status(graph_result: Any, node_name: str) -> str:
    node = graph_result.results.get(node_name)
    if node is None:
        return "skipped"
    error = getattr(node, "error", None)
    if error:
        return "failed"
    return "success"


def _build_distill_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは distillNode です。distill 以外の処理は禁止です。"
        "提案書作成・レビュー・再実行・全体サマリは出力しないでください。"
        "次のドキュメントを file_read(mode='view') で読み、蒸留結果を Markdown で file_write してください。"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力ドキュメント: {ctx['doc_path']}\n"
        f"保存先: {ctx['notes_path']}\n"
    )


def _build_proposal_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは proposalNode です。proposal 作成以外の処理は禁止です。"
        "distill/review/rerun の説明や実行宣言は出力しないでください。"
        "蒸留ノートを file_read(mode='view') で読み、章立て付き Markdown を file_write で保存してください。"
        "制約: 提案書本文 4000 文字以内、章は最大6つ、各節3〜5行。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"蒸留ノート: {ctx['notes_path']}\n"
        f"保存先: {ctx['proposal_path']}\n"
    )


def _build_story_map_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは storyMapNode です。story-map 以外の処理は禁止です。"
        "蒸留ノートをもとに、活動 > エピック > ストーリーの3層で story map を作成し、"
        "優先度(高/中/低)を各項目に付けて Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力ノート: {ctx['notes_path']}\n"
        f"保存先: {ctx['story_map_path']}\n"
    )


def _build_architecture_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは softwareArchitectureNode です。software-architecture 以外の処理は禁止です。"
        "story map と蒸留ノートから、代替案を2案以上比較し採用理由を明記した設計書を作成してください。"
        "非機能要件(性能/可用性/保守性/セキュリティ)を最低3項目含め、Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"story map: {ctx['story_map_path']}\n"
        f"蒸留ノート: {ctx['notes_path']}\n"
        f"保存先: {ctx['architecture_path']}\n"
    )


def _build_decision_framework_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは decisionFrameworkNode です。decision-framework 以外の処理は禁止です。"
        "設計書から ADR を作成し、決定/根拠/トレードオフ/リスクを必ず記載してください。"
        "日付と識別子を含む Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力設計書: {ctx['architecture_path']}\n"
        f"保存先: {ctx['adr_path']}\n"
    )


def _build_diagram_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは diagramNode です。diagram 以外の処理は禁止です。"
        "設計書から mermaid(flowchart または graph) を含む図解 Markdown を作成してください。"
        "図のノードは最低3つとし file_write で保存してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力設計書: {ctx['architecture_path']}\n"
        f"保存先: {ctx['diagram_path']}\n"
    )


def _build_effective_ts_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは effectiveTypeScriptNode です。effective-typescript 以外の処理は禁止です。"
        "sample.ts を読み、型安全の観点(any/unsafe/assertion等)で最低3件の具体指摘と修正案を作成してください。"
        "Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力コード: {ctx['sample_ts_path']}\n"
        f"保存先: {ctx['ts_review_path']}\n"
    )


def _build_robust_python_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは robustPythonNode です。robust-python 以外の処理は禁止です。"
        "既存成果物をもとに Python 実装時の堅牢性レビューを作成してください。"
        "例外処理/型/副作用/I-O境界の具体指摘を最低3件含め、Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力資料: {ctx['proposal_path']}\n"
        f"保存先: {ctx['py_review_path']}\n"
    )


def _build_test_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは testNode です。test 以外の処理は禁止です。"
        "TS/Pythonレビュー結果を入力に、正常/異常/境界の3分類を含むテスト計画を作成してください。"
        "ケースは6件以上とし Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"TSレビュー: {ctx['ts_review_path']}\n"
        f"Pythonレビュー: {ctx['py_review_path']}\n"
        f"保存先: {ctx['test_plan_path']}\n"
    )


def _build_review_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは reviewNode です。review 以外の処理は禁止です。"
        "distill/proposal/rerun/全体サマリの記述はしないでください。"
        "notes/proposal を file_read(mode='view') し、参照例を file_read(mode='view') して1〜2行引用し、"
        "レビュー結果を JSON で file_write してください。出力JSONに reviewer フィールドを含めないでください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"notes: {ctx['notes_path']}\n"
        f"proposal: {ctx['proposal_path']}\n"
        f"参照例: {ctx['review_example_path']}\n"
        f"保存先(JSON): {ctx['decision_path']}\n"
        f"review_id: {ctx['review_id']}\n"
        f"date(UTC): {ctx['date_utc']}\n"
    )


def _build_data_validation_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは dataValidationNode です。data-validation 以外の処理は禁止です。"
        "レビューJSONの必須キー・型・空値を検証し、結果をJSONで file_write してください。"
        "出力JSONは passed/failed/errors の3キーを持つこと。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力レビューJSON: {ctx['decision_path']}\n"
        f"保存先(JSON): {ctx['validation_report_path']}\n"
    )


def _build_agent_craft_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは agentCraftNode です。agent-craft 以外の処理は禁止です。"
        "成果物をもとにサブエージェント設計書を作成してください。"
        "各エージェントの責務/入力/出力/禁止事項を明記し、責務は2つ以上に分離してください。"
        "Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力: {ctx['proposal_path']}, {ctx['decision_path']}\n"
        f"保存先: {ctx['subagent_design_path']}\n"
    )


def _build_skill_forge_prompt(ctx: dict[str, str]) -> str:
    return (
        "あなたは skillForgeNode です。skill-forge 以外の処理は禁止です。"
        "検証成果物から再利用可能な新規スキル仕様を作成してください。"
        "name/use when/tools/inputs/outputs を必ず記載し、汎用手順を3ステップ以上含めて Markdown を file_write してください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"入力: {ctx['subagent_design_path']}, {ctx['validation_report_path']}\n"
        f"保存先: {ctx['new_skill_spec_path']}\n"
    )


def _build_rerun_prompt(ctx: dict[str, str], rerun_path: str) -> str:
    return (
        "あなたは rerunReviewNode です。再レビューのみ実行し、全体総括は出力しないでください。"
        "既存 notes/proposal を file_read(mode='view') で読んで、再レビュー結果を JSON で file_write してください。"
        "出力JSONには reviewer フィールドを含めないでください。\n"
        "最後に 1 行で stage/status/output_path のみ報告してください。\n"
        f"notes: {ctx['notes_path']}\n"
        f"proposal: {ctx['proposal_path']}\n"
        f"参照例: {ctx['review_example_path']}\n"
        f"保存先(JSON): {rerun_path}\n"
    )


def _build_recovery_prompt(failed_step: str, error_text: str) -> str:
    return (
        "あなたは recoveryNode です。失敗分類と再試行手順のみ返してください。"
        "以下の失敗内容を token/encoding/tool/env/unknown に分類し、"
        "retry_action を3つ以内で提示してください。\n"
        f"failed_step: {failed_step}\n"
        f"error: {error_text}\n"
    )


def build_graph(paths: VerifyPaths, model) -> tuple[Any, dict[str, str], str]:
    ctx = build_artifact_paths(paths)
    rerun_path = build_rerun_decision_path(paths)

    distill_agent = create_agent(paths, model, include_file_write=True)
    story_map_agent = create_agent(paths, model, include_file_write=True)
    software_arch_agent = create_agent(paths, model, include_file_write=True)
    decision_framework_agent = create_agent(paths, model, include_file_write=True)
    diagram_agent = create_agent(paths, model, include_file_write=True)
    effective_ts_agent = create_agent(paths, model, include_file_write=True)
    robust_python_agent = create_agent(paths, model, include_file_write=True)
    test_agent = create_agent(paths, model, include_file_write=True)
    proposal_agent = create_agent(paths, model, include_file_write=True)
    review_agent = create_agent(paths, model, include_file_write=True)
    data_validation_agent = create_agent(paths, model, include_file_write=True)
    agent_craft_agent = create_agent(paths, model, include_file_write=True)
    skill_forge_agent = create_agent(paths, model, include_file_write=True)
    rerun_agent = create_agent(paths, model, include_file_write=True)
    recovery_agent = create_agent(paths, model, include_file_write=False)

    builder = GraphBuilder()
    builder.add_node(distill_agent, "distillNode")
    builder.add_node(story_map_agent, "storyMapNode")
    builder.add_node(software_arch_agent, "softwareArchitectureNode")
    builder.add_node(decision_framework_agent, "decisionFrameworkNode")
    builder.add_node(diagram_agent, "diagramNode")
    builder.add_node(effective_ts_agent, "effectiveTypeScriptNode")
    builder.add_node(robust_python_agent, "robustPythonNode")
    builder.add_node(test_agent, "testNode")
    builder.add_node(proposal_agent, "proposalNode")
    builder.add_node(review_agent, "reviewNode")
    builder.add_node(data_validation_agent, "dataValidationNode")
    builder.add_node(agent_craft_agent, "agentCraftNode")
    builder.add_node(skill_forge_agent, "skillForgeNode")
    builder.add_node(rerun_agent, "rerunReviewNode")
    builder.add_node(recovery_agent, "recoveryNode")

    def _node_succeeded(state, node_name: str) -> bool:
        node = state.results.get(node_name)
        if node is None:
            return False
        return getattr(node, "error", None) is None

    def _node_failed(state, node_name: str) -> bool:
        node = state.results.get(node_name)
        if node is None:
            return False
        return getattr(node, "error", None) is not None

    # fail-fast flow: proceed only when the previous node succeeded.
    builder.add_edge("distillNode", "storyMapNode", condition=lambda s: _node_succeeded(s, "distillNode"))
    builder.add_edge("storyMapNode", "softwareArchitectureNode", condition=lambda s: _node_succeeded(s, "storyMapNode"))
    builder.add_edge("softwareArchitectureNode", "decisionFrameworkNode", condition=lambda s: _node_succeeded(s, "softwareArchitectureNode"))
    builder.add_edge("decisionFrameworkNode", "diagramNode", condition=lambda s: _node_succeeded(s, "decisionFrameworkNode"))
    builder.add_edge("diagramNode", "effectiveTypeScriptNode", condition=lambda s: _node_succeeded(s, "diagramNode"))
    builder.add_edge("effectiveTypeScriptNode", "robustPythonNode", condition=lambda s: _node_succeeded(s, "effectiveTypeScriptNode"))
    builder.add_edge("robustPythonNode", "testNode", condition=lambda s: _node_succeeded(s, "robustPythonNode"))
    builder.add_edge("testNode", "proposalNode", condition=lambda s: _node_succeeded(s, "testNode"))
    builder.add_edge("proposalNode", "reviewNode", condition=lambda s: _node_succeeded(s, "proposalNode"))
    builder.add_edge("reviewNode", "rerunReviewNode", condition=lambda s: _node_succeeded(s, "reviewNode"))
    builder.add_edge("rerunReviewNode", "dataValidationNode", condition=lambda s: _node_succeeded(s, "rerunReviewNode"))
    builder.add_edge("dataValidationNode", "agentCraftNode", condition=lambda s: _node_succeeded(s, "dataValidationNode"))
    builder.add_edge("agentCraftNode", "skillForgeNode", condition=lambda s: _node_succeeded(s, "agentCraftNode"))

    # recovery runs only for the node that actually failed.
    builder.add_edge("distillNode", "recoveryNode", condition=lambda s: _node_failed(s, "distillNode"))
    builder.add_edge("storyMapNode", "recoveryNode", condition=lambda s: _node_failed(s, "storyMapNode"))
    builder.add_edge("softwareArchitectureNode", "recoveryNode", condition=lambda s: _node_failed(s, "softwareArchitectureNode"))
    builder.add_edge("decisionFrameworkNode", "recoveryNode", condition=lambda s: _node_failed(s, "decisionFrameworkNode"))
    builder.add_edge("diagramNode", "recoveryNode", condition=lambda s: _node_failed(s, "diagramNode"))
    builder.add_edge("effectiveTypeScriptNode", "recoveryNode", condition=lambda s: _node_failed(s, "effectiveTypeScriptNode"))
    builder.add_edge("robustPythonNode", "recoveryNode", condition=lambda s: _node_failed(s, "robustPythonNode"))
    builder.add_edge("testNode", "recoveryNode", condition=lambda s: _node_failed(s, "testNode"))
    builder.add_edge("proposalNode", "recoveryNode", condition=lambda s: _node_failed(s, "proposalNode"))
    builder.add_edge("reviewNode", "recoveryNode", condition=lambda s: _node_failed(s, "reviewNode"))
    builder.add_edge("rerunReviewNode", "recoveryNode", condition=lambda s: _node_failed(s, "rerunReviewNode"))
    builder.add_edge("dataValidationNode", "recoveryNode", condition=lambda s: _node_failed(s, "dataValidationNode"))
    builder.add_edge("agentCraftNode", "recoveryNode", condition=lambda s: _node_failed(s, "agentCraftNode"))
    builder.add_edge("skillForgeNode", "recoveryNode", condition=lambda s: _node_failed(s, "skillForgeNode"))

    graph = builder.build()
    return graph, ctx, rerun_path


def run_graph(paths: VerifyPaths, model, mode: str = "full") -> WorkflowRunResult:
    graph, ctx, rerun_path = build_graph(paths, model)

    if mode == "chain-only":
        initial_prompt = (
            f"{_build_distill_prompt(ctx)}\n\n{_build_story_map_prompt(ctx)}\n\n{_build_architecture_prompt(ctx)}\n\n"
            f"{_build_decision_framework_prompt(ctx)}\n\n{_build_diagram_prompt(ctx)}\n\n"
            f"{_build_effective_ts_prompt(ctx)}\n\n{_build_robust_python_prompt(ctx)}\n\n{_build_test_prompt(ctx)}\n\n"
            f"{_build_proposal_prompt(ctx)}\n\n{_build_review_prompt(ctx)}\n\n{_build_data_validation_prompt(ctx)}\n\n"
            f"{_build_agent_craft_prompt(ctx)}\n\n{_build_skill_forge_prompt(ctx)}"
        )
    elif mode == "recovery-only":
        initial_prompt = _build_recovery_prompt("manual", "forced recovery test")
    else:
        initial_prompt = (
            f"{_build_distill_prompt(ctx)}\n\n{_build_story_map_prompt(ctx)}\n\n{_build_architecture_prompt(ctx)}\n\n"
            f"{_build_decision_framework_prompt(ctx)}\n\n{_build_diagram_prompt(ctx)}\n\n"
            f"{_build_effective_ts_prompt(ctx)}\n\n{_build_robust_python_prompt(ctx)}\n\n{_build_test_prompt(ctx)}\n\n"
            f"{_build_proposal_prompt(ctx)}\n\n{_build_review_prompt(ctx)}\n\n{_build_rerun_prompt(ctx, rerun_path)}\n\n"
            f"{_build_data_validation_prompt(ctx)}\n\n{_build_agent_craft_prompt(ctx)}\n\n{_build_skill_forge_prompt(ctx)}"
        )

    graph_result = graph(initial_prompt)
    remove_reviewer_field(ctx["decision_path"])
    remove_reviewer_field(rerun_path)

    def _exists(path: str) -> bool:
        return Path(path).exists()

    distill_status = _node_status(graph_result, "distillNode")
    story_map_status = _node_status(graph_result, "storyMapNode")
    architecture_status = _node_status(graph_result, "softwareArchitectureNode")
    decision_framework_status = _node_status(graph_result, "decisionFrameworkNode")
    diagram_status = _node_status(graph_result, "diagramNode")
    effective_ts_status = _node_status(graph_result, "effectiveTypeScriptNode")
    robust_python_status = _node_status(graph_result, "robustPythonNode")
    test_status = _node_status(graph_result, "testNode")
    proposal_status = _node_status(graph_result, "proposalNode")
    review_status = _node_status(graph_result, "reviewNode")
    rerun_status = _node_status(graph_result, "rerunReviewNode")
    data_validation_status = _node_status(graph_result, "dataValidationNode")
    agent_craft_status = _node_status(graph_result, "agentCraftNode")
    skill_forge_status = _node_status(graph_result, "skillForgeNode")
    recovery_status = _node_status(graph_result, "recoveryNode")

    if mode == "chain-only":
        rerun_status = "skipped"
    if mode == "recovery-only":
        distill_status = "skipped"
        story_map_status = "skipped"
        architecture_status = "skipped"
        decision_framework_status = "skipped"
        diagram_status = "skipped"
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"

    # strict status: model error + required artifact existence
    if distill_status == "success" and not _exists(ctx["notes_path"]):
        distill_status = "failed"
    if story_map_status == "success" and not _exists(ctx["story_map_path"]):
        story_map_status = "failed"
    if architecture_status == "success" and not _exists(ctx["architecture_path"]):
        architecture_status = "failed"
    if decision_framework_status == "success" and not _exists(ctx["adr_path"]):
        decision_framework_status = "failed"
    if diagram_status == "success" and not _exists(ctx["diagram_path"]):
        diagram_status = "failed"
    if effective_ts_status == "success" and not _exists(ctx["ts_review_path"]):
        effective_ts_status = "failed"
    if robust_python_status == "success" and not _exists(ctx["py_review_path"]):
        robust_python_status = "failed"
    if test_status == "success" and not _exists(ctx["test_plan_path"]):
        test_status = "failed"
    if proposal_status == "success" and not _exists(ctx["proposal_path"]):
        proposal_status = "failed"
    if review_status == "success" and not _exists(ctx["decision_path"]):
        review_status = "failed"
    if mode == "full" and rerun_status == "success" and not _exists(rerun_path):
        rerun_status = "failed"
    if data_validation_status == "success" and not _exists(ctx["validation_report_path"]):
        data_validation_status = "failed"
    if agent_craft_status == "success" and not _exists(ctx["subagent_design_path"]):
        agent_craft_status = "failed"
    if skill_forge_status == "success" and not _exists(ctx["new_skill_spec_path"]):
        skill_forge_status = "failed"

    quality_nodes: dict[str, dict[str, Any]] = {
        "distillNode": {"pass": True, "reasons": [], "metrics": {}},
        "storyMapNode": {"pass": True, "reasons": [], "metrics": {}},
        "softwareArchitectureNode": {"pass": True, "reasons": [], "metrics": {}},
        "decisionFrameworkNode": {"pass": True, "reasons": [], "metrics": {}},
        "diagramNode": {"pass": True, "reasons": [], "metrics": {}},
        "effectiveTypeScriptNode": {"pass": True, "reasons": [], "metrics": {}},
        "robustPythonNode": {"pass": True, "reasons": [], "metrics": {}},
        "testNode": {"pass": True, "reasons": [], "metrics": {}},
        "proposalNode": {"pass": True, "reasons": [], "metrics": {}},
        "reviewNode": {"pass": True, "reasons": [], "metrics": {}},
        "rerunReviewNode": {"pass": True, "reasons": [], "metrics": {}},
        "dataValidationNode": {"pass": True, "reasons": [], "metrics": {}},
        "agentCraftNode": {"pass": True, "reasons": [], "metrics": {}},
        "skillForgeNode": {"pass": True, "reasons": [], "metrics": {}},
    }
    if story_map_status == "success":
        quality_nodes["storyMapNode"] = _check_story_map_quality(ctx["story_map_path"])
        if not quality_nodes["storyMapNode"]["pass"]:
            story_map_status = "failed"
    if architecture_status == "success":
        quality_nodes["softwareArchitectureNode"] = _check_architecture_quality(ctx["architecture_path"])
        if not quality_nodes["softwareArchitectureNode"]["pass"]:
            architecture_status = "failed"
    if decision_framework_status == "success":
        quality_nodes["decisionFrameworkNode"] = _check_decision_framework_quality(ctx["adr_path"])
        if not quality_nodes["decisionFrameworkNode"]["pass"]:
            decision_framework_status = "failed"
    if diagram_status == "success":
        quality_nodes["diagramNode"] = _check_diagram_quality(ctx["diagram_path"])
        if not quality_nodes["diagramNode"]["pass"]:
            diagram_status = "failed"
    if effective_ts_status == "success":
        quality_nodes["effectiveTypeScriptNode"] = _check_effective_ts_quality(ctx["ts_review_path"])
        if not quality_nodes["effectiveTypeScriptNode"]["pass"]:
            effective_ts_status = "failed"
    if robust_python_status == "success":
        quality_nodes["robustPythonNode"] = _check_robust_python_quality(ctx["py_review_path"])
        if not quality_nodes["robustPythonNode"]["pass"]:
            robust_python_status = "failed"
    if test_status == "success":
        quality_nodes["testNode"] = _check_test_quality(ctx["test_plan_path"])
        if not quality_nodes["testNode"]["pass"]:
            test_status = "failed"

    if distill_status == "success":
        quality_nodes["distillNode"] = _check_distill_quality(ctx["notes_path"])
        if not quality_nodes["distillNode"]["pass"]:
            distill_status = "failed"
    if proposal_status == "success":
        quality_nodes["proposalNode"] = _check_proposal_quality(ctx["proposal_path"])
        if not quality_nodes["proposalNode"]["pass"]:
            proposal_status = "failed"
    if review_status == "success":
        quality_nodes["reviewNode"] = _check_review_quality(ctx["decision_path"])
        if not quality_nodes["reviewNode"]["pass"]:
            review_status = "failed"
    if mode == "full" and rerun_status == "success":
        quality_nodes["rerunReviewNode"] = _check_review_quality(rerun_path)
        if not quality_nodes["rerunReviewNode"]["pass"]:
            rerun_status = "failed"
    if data_validation_status == "success":
        quality_nodes["dataValidationNode"] = _check_data_validation_quality(ctx["validation_report_path"])
        if not quality_nodes["dataValidationNode"]["pass"]:
            data_validation_status = "failed"
    if agent_craft_status == "success":
        quality_nodes["agentCraftNode"] = _check_agent_craft_quality(ctx["subagent_design_path"])
        if not quality_nodes["agentCraftNode"]["pass"]:
            agent_craft_status = "failed"
    if skill_forge_status == "success":
        quality_nodes["skillForgeNode"] = _check_skill_forge_quality(ctx["new_skill_spec_path"])
        if not quality_nodes["skillForgeNode"]["pass"]:
            skill_forge_status = "failed"

    failed_step = ""
    failed_error = ""
    for name, status in (
        ("distillNode", distill_status),
        ("storyMapNode", story_map_status),
        ("softwareArchitectureNode", architecture_status),
        ("decisionFrameworkNode", decision_framework_status),
        ("diagramNode", diagram_status),
        ("effectiveTypeScriptNode", effective_ts_status),
        ("robustPythonNode", robust_python_status),
        ("testNode", test_status),
        ("proposalNode", proposal_status),
        ("reviewNode", review_status),
        ("rerunReviewNode", rerun_status),
        ("dataValidationNode", data_validation_status),
        ("agentCraftNode", agent_craft_status),
        ("skillForgeNode", skill_forge_status),
    ):
        if status == "failed":
            failed_step = name
            break

    if failed_step:
        node = graph_result.results.get(failed_step)
        err = getattr(node, "error", None) if node is not None else None
        if err:
            failed_error = str(err)
        else:
            quality_reason = quality_nodes.get(failed_step, {}).get("reasons", [])
            if quality_reason:
                failed_error = "; ".join(quality_reason)
            else:
                failed_error = "required artifact not generated"

    # fail-fast status normalization: downstream nodes are treated as skipped.
    if failed_step == "distillNode":
        story_map_status = "skipped"
        architecture_status = "skipped"
        decision_framework_status = "skipped"
        diagram_status = "skipped"
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "storyMapNode":
        architecture_status = "skipped"
        decision_framework_status = "skipped"
        diagram_status = "skipped"
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "softwareArchitectureNode":
        decision_framework_status = "skipped"
        diagram_status = "skipped"
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "decisionFrameworkNode":
        diagram_status = "skipped"
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "diagramNode":
        effective_ts_status = "skipped"
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "effectiveTypeScriptNode":
        robust_python_status = "skipped"
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "robustPythonNode":
        test_status = "skipped"
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "testNode":
        proposal_status = "skipped"
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "proposalNode":
        review_status = "skipped"
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "reviewNode":
        rerun_status = "skipped"
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "rerunReviewNode":
        data_validation_status = "skipped"
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "dataValidationNode":
        agent_craft_status = "skipped"
        skill_forge_status = "skipped"
    elif failed_step == "agentCraftNode":
        skill_forge_status = "skipped"

    recovery_output = extract_text(graph_result.results.get("recoveryNode"))
    error_type = classify_exception(Exception(failed_error)) if failed_error else ""
    retry_action = ""
    if error_type == "token":
        retry_action = "出力制約を強化し、失敗ノードのみ再実行"
    elif error_type == "encoding":
        retry_action = "python -X utf8 で再実行し、対象ファイルの UTF-8 を確認"
    elif error_type == "tool":
        retry_action = "file_read/file_write の対象パスとパラメータを確認して再実行"
    elif error_type == "env":
        retry_action = "AWS_* 環境変数を確認して再実行"
    elif failed_step:
        retry_action = "失敗ノードを最小入力で再実行"

    if failed_step and recovery_status == "skipped":
        recovery_status = "failed"

    required_statuses = [
        distill_status,
        story_map_status,
        architecture_status,
        decision_framework_status,
        diagram_status,
        effective_ts_status,
        robust_python_status,
        test_status,
        proposal_status,
        review_status,
        data_validation_status,
        agent_craft_status,
        skill_forge_status,
    ]
    if mode == "full":
        required_statuses.append(rerun_status)
    if mode == "recovery-only":
        required_statuses = [recovery_status]

    summary = {
        "generated_at_utc": utc_now_iso(),
        "mode": mode,
        "status": "pass" if all(s == "success" for s in required_statuses) else "fail",
        "nodes": {
            "distillNode": {"status": distill_status, "artifact_exists": _exists(ctx["notes_path"])},
            "storyMapNode": {"status": story_map_status, "artifact_exists": _exists(ctx["story_map_path"])},
            "softwareArchitectureNode": {"status": architecture_status, "artifact_exists": _exists(ctx["architecture_path"])},
            "decisionFrameworkNode": {"status": decision_framework_status, "artifact_exists": _exists(ctx["adr_path"])},
            "diagramNode": {"status": diagram_status, "artifact_exists": _exists(ctx["diagram_path"])},
            "effectiveTypeScriptNode": {"status": effective_ts_status, "artifact_exists": _exists(ctx["ts_review_path"])},
            "robustPythonNode": {"status": robust_python_status, "artifact_exists": _exists(ctx["py_review_path"])},
            "testNode": {"status": test_status, "artifact_exists": _exists(ctx["test_plan_path"])},
            "proposalNode": {"status": proposal_status, "artifact_exists": _exists(ctx["proposal_path"])},
            "reviewNode": {"status": review_status, "artifact_exists": _exists(ctx["decision_path"])},
            "rerunReviewNode": {
                "status": rerun_status,
                "artifact_exists": _exists(rerun_path),
                "decision_path": rerun_path,
            },
            "dataValidationNode": {"status": data_validation_status, "artifact_exists": _exists(ctx["validation_report_path"])},
            "agentCraftNode": {"status": agent_craft_status, "artifact_exists": _exists(ctx["subagent_design_path"])},
            "skillForgeNode": {"status": skill_forge_status, "artifact_exists": _exists(ctx["new_skill_spec_path"])},
            "recoveryNode": {"status": recovery_status},
        },
        "artifacts": {
            "notes_path": ctx["notes_path"],
            "story_map_path": ctx["story_map_path"],
            "architecture_path": ctx["architecture_path"],
            "adr_path": ctx["adr_path"],
            "diagram_path": ctx["diagram_path"],
            "sample_ts_path": ctx["sample_ts_path"],
            "ts_review_path": ctx["ts_review_path"],
            "py_review_path": ctx["py_review_path"],
            "test_plan_path": ctx["test_plan_path"],
            "proposal_path": ctx["proposal_path"],
            "decision_path": ctx["decision_path"],
            "rerun_decision_path": rerun_path,
            "validation_report_path": ctx["validation_report_path"],
            "subagent_design_path": ctx["subagent_design_path"],
            "new_skill_spec_path": ctx["new_skill_spec_path"],
        },
        "failure": {
            "failed_stage": failed_step,
            "error_type": error_type,
            "error_message": failed_error,
            "recovery_output": recovery_output,
            "retry_action": retry_action,
        },
        "quality_gate": {
            "status": "pass" if all(v.get("pass", False) for v in quality_nodes.values()) else "fail",
            "nodes": quality_nodes,
        },
    }

    graph_text_results: dict[str, dict[str, Any]] = {
        "distillNode": {
            "stage": "distill",
            "status": distill_status,
            "output_path": ctx["notes_path"],
            "error": failed_error if failed_step == "distillNode" else "",
        },
        "storyMapNode": {
            "stage": "story-map",
            "status": story_map_status,
            "output_path": ctx["story_map_path"],
            "error": failed_error if failed_step == "storyMapNode" else "",
        },
        "softwareArchitectureNode": {
            "stage": "software-architecture",
            "status": architecture_status,
            "output_path": ctx["architecture_path"],
            "error": failed_error if failed_step == "softwareArchitectureNode" else "",
        },
        "decisionFrameworkNode": {
            "stage": "decision-framework",
            "status": decision_framework_status,
            "output_path": ctx["adr_path"],
            "error": failed_error if failed_step == "decisionFrameworkNode" else "",
        },
        "diagramNode": {
            "stage": "diagram",
            "status": diagram_status,
            "output_path": ctx["diagram_path"],
            "error": failed_error if failed_step == "diagramNode" else "",
        },
        "effectiveTypeScriptNode": {
            "stage": "effective-typescript",
            "status": effective_ts_status,
            "output_path": ctx["ts_review_path"],
            "error": failed_error if failed_step == "effectiveTypeScriptNode" else "",
        },
        "robustPythonNode": {
            "stage": "robust-python",
            "status": robust_python_status,
            "output_path": ctx["py_review_path"],
            "error": failed_error if failed_step == "robustPythonNode" else "",
        },
        "testNode": {
            "stage": "test",
            "status": test_status,
            "output_path": ctx["test_plan_path"],
            "error": failed_error if failed_step == "testNode" else "",
        },
        "proposalNode": {
            "stage": "proposal",
            "status": proposal_status,
            "output_path": ctx["proposal_path"],
            "error": failed_error if failed_step == "proposalNode" else "",
        },
        "reviewNode": {
            "stage": "review",
            "status": review_status,
            "output_path": ctx["decision_path"],
            "error": failed_error if failed_step == "reviewNode" else "",
        },
        "rerunReviewNode": {
            "stage": "rerun",
            "status": rerun_status,
            "output_path": rerun_path,
            "error": failed_error if failed_step == "rerunReviewNode" else "",
        },
        "dataValidationNode": {
            "stage": "data-validation",
            "status": data_validation_status,
            "output_path": ctx["validation_report_path"],
            "error": failed_error if failed_step == "dataValidationNode" else "",
        },
        "agentCraftNode": {
            "stage": "agent-craft",
            "status": agent_craft_status,
            "output_path": ctx["subagent_design_path"],
            "error": failed_error if failed_step == "agentCraftNode" else "",
        },
        "skillForgeNode": {
            "stage": "skill-forge",
            "status": skill_forge_status,
            "output_path": ctx["new_skill_spec_path"],
            "error": failed_error if failed_step == "skillForgeNode" else "",
        },
        "recoveryNode": {
            "stage": "recovery",
            "status": recovery_status,
            "output_path": "",
            "error": "",
        },
    }

    return WorkflowRunResult(status=summary["status"], summary=summary, graph_results=graph_text_results)

