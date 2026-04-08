# strands-py ランタイム（incident-response）

本スキルは **SLO/SLI・対応フロー・ポストモーテム・プレイブック**など設計ドキュメントが中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の既存運用メモ、過去のポストモーテム、SLI 定義のたたき台を読む。
- **`file_write`**: SLO 定義書、監視設計、オンコール設計、ICS フロー、ポストモーテムテンプレート、プレイブックを `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の SRE プラクティス確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- 蒸留ノート（`skills-machine/...`）は workspace に無い場合はユーザー提供の抜粋またはヒアリングで補う。

## 連携スキル（Strands での読み替え）

- **observability**: OpenTelemetry・バーンアラート等の **計装・オブザーバビリティ設計**は observability スキル側。本スキルはエラーバジェット運用・インシデントプロセスが主。
- **diagram**: エスカレーション経路・構成図は diagram 用の strands ランタイム説明に従う。
- **agent-craft**（pr）は Strands では除外。**対応自動化エージェントの YAML 実装**は **dev の agent-craft-strands** を参照する。
