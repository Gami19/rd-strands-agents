# strands-py ランタイム（onboarding）

本スキルは **学習ロードマップ・クイズ・メンタリング・進捗レポート**など対話と Markdown 成果物が中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内のチェックリスト、社内ドキュメントの抜粋（ユーザーが配置した場合）、進捗メモを読む。
- **`file_write`**: ロードマップ、スコアレポート、1on1 準備シート、進捗サマリーを `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- SKILL 本文の **KC 全21本**や `project/00_schemas/...` はリポジトリ構成に依存する。workspace に無い場合はユーザー提供の要約・ヒアリングで補う。

## スキル管理（skill-forge）

- **skill-forge**（pr）は Strands では **無効化**されている。スキル鋳造・バージョン管理のワークフローは IDE / Claude Code 前提の別作業として扱う。
