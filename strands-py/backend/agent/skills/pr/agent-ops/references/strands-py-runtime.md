# strands-py ランタイム（agent-ops）

本スキルは **運用設計・評価指標・ランブック・ガードレールの文書化**が主目的です。`references/` 内の **bash / pip / Python スニペット**（例: `monitoring-guide.md` の AgentOps・LangSmith セットアップ）は、**書籍・プロダクトの手順例**であり、strands-py の Agent からは **自動実行されません**。

## strands-py での進め方

- **`file_read` / `file_write`**: 評価メトリクス定義、ガードレール設計、運用ランブックを `notes/` や `proposal/` に Markdown で保存・更新する。
- **監視ツールの実装**: 本リポジトリのランタイムが AgentOps / LangSmith に自動接続するわけではない。設計書では「自環境でのセットアップ手順」として references のコードブロックを引用し、**人間または別パイプライン**が実行する前提で書く。

## 利用可能なツール

エージェント定義の `allowed_tools` に含まれる範囲で `file_read` / `file_write` / `workspace_list`（および許可されていれば `web_fetch_text` 等）を使う。

## 関連スキル（実装・図）

- 構成図が必要なら **diagram**（Strands では `diagram_generate_drawio` 等。dev の diagram スキル内 runtime 説明を参照）。
- Claude Code でのカスタムエージェント実装は **pr の agent-craft は Strands で除外**。strands-py 利用時は **dev の agent-craft-strands** を参照。
