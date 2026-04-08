"""Skills policy and filtering for Strands runtime.

フィールドの意味（コード上の正）:

- excluded: True のスキルは skills_root に存在しても build_filtered_skills_root のコピー対象外。
  ランタイムの AgentSkills には載らない。
- adapter: SKILL 本文の加工パイプラインを識別する文字列（任意）。
  WIRED_SKILL_ADAPTERS に含まれる ID は「strands-py 側で代替手段が用意済み」を意味する。
  例: pdf/diagram は compat ツール（pdf_convert_to_inbox / diagram_generate_drawio）と KC の references/strands-py-runtime.md で整合。SKILL 全文の自動書き換えは行わない。
- requires: スキルが前提とする外部能力のタグ（bash, ide など）。説明・カタログ用。
- fallback: 利用者向けの短い説明（README / GET /api/skills/catalog など）。

build_filtered_skills_root は excluded のみを参照する。SKILL_POLICIES に無いディレクトリ名は
policy_for でデフォルトポリシー（excluded=False, adapter=None）になる。
memory/skills-strategy.md のフェーズ0/3 と整合させる。
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# strands-py がランタイムで代替実装している adapter ID（カタログの adapter_wired と一致）。
WIRED_SKILL_ADAPTERS: frozenset[str] = frozenset(
    {
        "pdf_convert_backend_tool",
        "diagram_write_mapping",
    }
)


@dataclass(frozen=True)
class SkillPolicy:
    """1 スキルディレクトリに対する Strands 側の方針。

    excluded: ランタイムに載せないか。
    adapter: パイプライン ID。None はアダプタ不要（常に adapter_wired 相当）。
    requires: 前提タプル（カタログ・説明用）。
    fallback: 利用者向けの一行説明。
    """

    excluded: bool
    adapter: str | None
    requires: tuple[str, ...]
    fallback: str


SKILL_POLICIES: dict[str, SkillPolicy] = {
    "agent-craft": SkillPolicy(
        excluded=True,
        adapter=None,
        requires=("ide", "claude"),
        fallback="Claude Code 専用のため Strands では無効化されています。",
    ),
    "skill-forge": SkillPolicy(
        excluded=True,
        adapter=None,
        requires=("ide", "claude", "bash"),
        fallback="依存するワークフローが Strands 未対応のため無効化されています。",
    ),
    "pdf-convert": SkillPolicy(
        excluded=False,
        adapter="pdf_convert_backend_tool",
        requires=("bash",),
        fallback="Strands では pdf_convert_to_inbox（docling 要）。詳細はスキル内 references/strands-py-runtime.md。",
    ),
    "diagram": SkillPolicy(
        excluded=False,
        adapter="diagram_write_mapping",
        requires=("write",),
        fallback="Strands では diagram_generate_drawio（proposal 配下）。詳細は references/strands-py-runtime.md。",
    ),
    "ad-creative": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="workspace の file_read / file_write で CSV・成果物を扱う。references/strands-py-runtime.md。",
    ),
    "agent-ops": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="設計・ランブックは Markdown を workspace に。references の bash は例示のみ。strands-py-runtime.md。",
    ),
    "ai-agents": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="設計書は workspace に。実装は dev の agent-craft-strands（pr の agent-craft は除外）。strands-py-runtime.md。",
    ),
    "comm-craft": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="コミュニケーション成果物は workspace の file_read / file_write。agent 実装は agent-craft-strands。strands-py-runtime.md。",
    ),
    "growth-ops": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="marketing-context・CSV・レポートは workspace。references の Python は例示。strands-py-runtime.md。",
    ),
    "incident-response": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="SLO・プレイブック等は workspace。observability・diagram と分担。strands-py-runtime.md。",
    ),
    "observability": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="OTel・OMM・パイプライン設計は workspace。references の YAML は例示。strands-py-runtime.md。",
    ),
    "onboarding": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="ロードマップ・レポートは workspace。skill-forge は無効。strands-py-runtime.md。",
    ),
    "project-ops": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="フロー・DORA・再編成計画は workspace。strands-py-runtime.md。",
    ),
    "seo-analytics": SkillPolicy(
        excluded=False,
        adapter=None,
        requires=("workspace",),
        fallback="監査・GA4/GTM 設計は workspace。コード例は実装向け。strands-py-runtime.md。",
    ),
}


def adapter_wired(adapter: str | None) -> bool:
    if adapter is None:
        return True
    return adapter in WIRED_SKILL_ADAPTERS


def policy_for(skill_name: str) -> SkillPolicy:
    return SKILL_POLICIES.get(
        skill_name,
        SkillPolicy(
            excluded=False,
            adapter=None,
            requires=(),
            fallback="未対応前提がある場合は代替案を提示します。",
        ),
    )


def excluded_skill_names() -> set[str]:
    return {name for name, p in SKILL_POLICIES.items() if p.excluded}


def list_skill_catalog(skills_root: Path) -> list[dict[str, Any]]:
    """skills_root 直下の SKILL.md 付きディレクトリを列挙し、解決後ポリシーを付与する。"""
    if not skills_root.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if not (child / "SKILL.md").is_file():
            continue
        skill_id = child.name
        p = policy_for(skill_id)
        out.append(
            {
                "skill_id": skill_id,
                "excluded": p.excluded,
                "included_in_runtime": not p.excluded,
                "adapter": p.adapter,
                "adapter_wired": adapter_wired(p.adapter),
                "requires": list(p.requires),
                "fallback": p.fallback,
            }
        )
    return out


def build_filtered_skills_root(skills_root: Path) -> Path:
    if not skills_root.is_dir():
        raise ValueError(f"有効な skills_root ではありません: {skills_root}")

    excluded = excluded_skill_names()
    candidates: list[Path] = []
    for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name in excluded:
            continue
        if not (child / "SKILL.md").is_file():
            continue
        candidates.append(child)

    if not candidates:
        raise ValueError("有効なスキルが見つかりません（除外設定を確認してください）")

    sig_source = "|".join(
        f"{p.name}:{(p / 'SKILL.md').stat().st_mtime_ns}" for p in candidates
    )
    sig = hashlib.sha256(
        f"{skills_root.resolve()}|{','.join(sorted(excluded))}|{sig_source}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    cache_root = Path(tempfile.gettempdir()) / "strands-skills-filtered"
    out_root = cache_root / sig
    if out_root.is_dir():
        return out_root

    tmp_root = cache_root / f"{sig}.tmp"
    if tmp_root.exists():
        shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    for src in candidates:
        shutil.copytree(src, tmp_root / src.name)

    tmp_root.replace(out_root)
    return out_root


def build_selected_skills_root(filtered_skills_root: Path, selected_skills: tuple[str, ...]) -> Path:
    """
    excluded 適用後の skills ルートから、指定された skill だけを抽出したルートを返す。
    selected_skills が空なら filtered_skills_root をそのまま返す。
    """
    if not selected_skills:
        return filtered_skills_root
    if not filtered_skills_root.is_dir():
        raise ValueError(f"有効な filtered_skills_root ではありません: {filtered_skills_root}")

    available = {
        p.name: p
        for p in filtered_skills_root.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    }
    missing = [s for s in selected_skills if s not in available]
    if missing:
        raise ValueError(
            "指定された skills が見つかりません（除外済みまたは存在しない可能性）: "
            + ", ".join(missing)
        )

    sig_source = "|".join(
        f"{available[s].name}:{(available[s] / 'SKILL.md').stat().st_mtime_ns}"
        for s in selected_skills
    )
    sig = hashlib.sha256(
        f"{filtered_skills_root.resolve()}|{','.join(selected_skills)}|{sig_source}".encode("utf-8")
    ).hexdigest()[:16]

    cache_root = Path(tempfile.gettempdir()) / "strands-skills-selected"
    out_root = cache_root / sig
    if out_root.is_dir():
        return out_root

    tmp_root = cache_root / f"{sig}.tmp"
    if tmp_root.exists():
        shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    for s in selected_skills:
        shutil.copytree(available[s], tmp_root / s)

    tmp_root.replace(out_root)
    return out_root
