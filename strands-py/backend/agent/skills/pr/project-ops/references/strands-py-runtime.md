# strands-py ランタイム（project-ops）

本スキルは **依存分析・認知負荷・TOC・DORA・Dynamic Reteaming**など Markdown レポートが中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の現状メモ、メトリクス抜粋、過去の改善計画を読む。
- **`file_write`**: 依存関係レポート、認知負荷マトリクス、TOC 改善計画、DORA ロードマップ、再編成計画を `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の DORA・フロー改善の参照に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。

## 連携スキル

- **flow-architecture**: 上流の戦略設計。本スキルは運用・戦術レベルのフロー最適化。
- **diagram**: VSM・依存関係図・チーム構成図は diagram 用の strands ランタイム説明に従う。
- **incident-response** / **observability**: MTTR 改善の具体策（プレイブック・SLO アラート等）との分担は各スキルの runtime 参照に従う。
