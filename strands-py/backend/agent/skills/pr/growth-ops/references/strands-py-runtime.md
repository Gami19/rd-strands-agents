# strands-py ランタイム（growth-ops）

本スキルは **ファネル分析・CRO・実験設計・レポート**が中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の `marketing-context.md`、ユーザーがアップロードした CSV・レポート抜粋（`inbox/` 等）、既存の分析メモを読む。
- **`file_write`**: ファネル分析、実験バックログ、CRO 提案、広告分析レポートを `notes/` または `proposal/` に Markdown / CSV で保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の計測・CRO ベンチマークの確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- Step 1 の `marketing-context.md` は **workspace 内**を `file_read` で探す。無ければユーザーへのヒアリングで補う（SKILL 本文どおり）。

## references 内のコード

- [cohort-analysis-guide.md](cohort-analysis-guide.md) 等の **Python/pandas スニペットはローカル分析の例示**である。Strands Agent から自動実行される前提ではない。必要ならユーザーが別環境で実行するか、分析結果を workspace に置いて `file_read` する形に読み替える。

## 補完スキル

- **diagram** でファネル図・ダッシュボード構成図が必要な場合は、diagram 用の strands ランタイム説明に従う。
