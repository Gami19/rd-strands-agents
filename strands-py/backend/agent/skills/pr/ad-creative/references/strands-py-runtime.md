# strands-py ランタイム（ad-creative）

本スキルは **マーケティング判断・コピー生成・表形式出力**が中心で、Claude Code 専用コマンドは前提としていません。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の `marketing-context.md`、ユーザーがアップロードした CSV（`inbox/` 等）、既存の広告データを読む。
- **`file_write`**: クリエイティブマトリクス・分析レポートを `notes/` または `proposal/` に Markdown / CSV で保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の仕様・ベンチマーク確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- Step 1 の `marketing-context.md` はリポジトリ直下ではなく **上記 workspace 内**を `file_read` で探す。無ければユーザーへのヒアリングで補う（SKILL 本文どおり）。

## 注意

- 本スキル本文の **CSV 取り込み**は、ユーザーが UI からファイルを添付したパス、または workspace に置いたファイルを `file_read` で読む形に読み替える。
- **`diagram` スキル**でキャンペーン図を作る場合は、diagram 用の strands ランタイム説明（dev/diagram）に従う。
