# strands-py ランタイム（comm-craft）

本スキルは **聴衆分析・メッセージ構造・交渉戦略・プレゼン骨格**など Markdown 成果物が中心で、Claude Code 専用コマンドは前提としていない。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の既存メモ、ADR、要件メモを読む。
- **`file_write`**: 聴衆分析表、メッセージ構造、交渉シナリオ、プレゼン骨格を `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の交渉・プレゼン理論の確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- 蒸留ノートや原典パス（`skills-machine/...`）はリポジトリ構成に依存する。workspace に無い場合はユーザー提供の抜粋またはヒアリングで補う。

## 下流スキル

- **PPTX 化**は slide-gen / kc-slide-gen 等の別スキル・別ツール前提。Strands では該当ツールが無ければ Markdown 骨格までを成果とする。

## 連携（エージェント実装）

- **agent-craft**（pr）は Strands では除外される。**YAML ベースのエージェント実装**が必要な場合は **dev の agent-craft-strands** を参照する。
