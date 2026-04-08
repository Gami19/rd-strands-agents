"""フェーズ5: pr スキルの Strands 向け明示ポリシー（段階1〜3）。"""

from __future__ import annotations

from src.infrastructure.skill_policy import policy_for


def test_phase5_skills_not_excluded() -> None:
    for name in (
        "ad-creative",
        "agent-ops",
        "ai-agents",
        "comm-craft",
        "growth-ops",
        "incident-response",
        "observability",
        "onboarding",
        "project-ops",
        "seo-analytics",
    ):
        p = policy_for(name)
        assert p.excluded is False
        assert "strands-py-runtime" in p.fallback or "workspace" in p.fallback
