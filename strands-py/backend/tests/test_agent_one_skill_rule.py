"""1 スキル = 1 エージェント: single YAML の skills 複数指定を拒否する。"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.infrastructure.agent_definitions import load_single_agent_definition


def test_load_single_rejects_multiple_skills(tmp_path: Path) -> None:
    agents = tmp_path / "agents"
    agents.mkdir(parents=True)
    (agents / "two.yaml").write_text(
        """
kind: single
name: Bad
description: x
system_prompt: test
allowed_tools:
  - file_read
skills:
  - marketing-copy
  - onboarding
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="1 スキル"):
        load_single_agent_definition(tmp_path, "two")
