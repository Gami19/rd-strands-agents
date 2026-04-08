# strands-py ランタイム（ai-agents）

本スキルは **Five Pillars に基づく設計・アーキテクチャ選定**が中心です。strands-py では **設計成果物を workspace 上の Markdown に落とす**ことにフォーカスする。

## 実装フェーズの読み替え

| KC / 本文の記述 | strands-py での扱い |
|:---|:---|
| **agent-craft**（Claude Code `.claude/agents/`） | **pr の agent-craft は Strands ランタイムから除外**されている。実装手順が必要なら **dev スキル `agent-craft-strands`**（エージェント YAML・Strands 向け）を使う。 |
| **skill-forge** | **pr の skill-forge も除外**。スキル作成は別途、手作業または将来のワークフローで扱う。 |
| **diagram** | 構成図は diagram スキル＋`diagram_generate_drawio` 等（dev/diagram の runtime 説明参照）。 |

## 利用可能なツール

エージェント定義の `allowed_tools` に従い、通常は **`file_read` / `file_write`** で設計書・比較表を `notes/` や `proposal/` に出力する。`web_fetch_text` が許可されていれば外部ドキュメントの参照に使える。

## 作業領域

- `DATA_ROOT/projects/<project_id>/` 配下がプロジェクトの正。設計の「単一のソース」はここに保存し、後続の review / diagram と共有する。
