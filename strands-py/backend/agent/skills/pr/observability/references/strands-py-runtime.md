# strands-py ランタイム（observability）

本スキルは **OMM 評価・構造化イベント・OTel 計装・サンプリング・テレメトリパイプライン**など設計ドキュメントとコード例が中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の既存設計メモ、SLO 案、パイプライン構成のたたきを読む。
- **`file_write`**: オブザーバビリティ設計書、OTel 計装ガイド、SLO 定義、サンプリング方針を `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の OTel・OMM 資料の確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。

## references 内の YAML・コード

- [otel-collector-configs.md](otel-collector-configs.md) 等の **Collector マニフェスト・OTel 設定は実装・デプロイ先向けの例示**である。Strands Agent からクラスタへ適用される前提ではない。必要ならユーザーが別環境で実行するか、成果物を workspace に置いて `file_read` する形に読み替える。

## 連携スキル（Strands での読み替え）

- **incident-response**: エラーバジェット運用・インシデント対応プロセス。本スキルはイベントベース SLI・バーンアラート・OTel 計装の設計側が主。
- **diagram**: パイプライン構成図・トレースフロー図は diagram 用の strands ランタイム説明に従う。
- **agent-craft**（pr）は Strands では除外。**エージェント設計に OTel を組み込む場合**の YAML 実装は **dev の agent-craft-strands** を参照する。
