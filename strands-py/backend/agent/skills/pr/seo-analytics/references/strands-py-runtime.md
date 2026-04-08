# strands-py ランタイム（seo-analytics）

本スキルは **技術SEO監査・AI検索・GA4/GTM・構造化データ・A/B 設計**などレポートと設計書が中心。strands-py では次を正とする。

## 利用可能なツール（エージェント YAML の `allowed_tools` に従う）

典型的には次が使える（プロジェクトのエージェント定義でホワイトリストされる）:

- **`file_read`**: workspace 内の `marketing-context.md` や `.claude/product-marketing-context.md` 相当のパス（ユーザーが置いたファイル）、Search Console / GA4 のエクスポート（CSV 等）を読む。
- **`file_write`**: 監査レポート、コンテンツ戦略、JSON-LD 案、GA4/GTM 設計書、A/B 設計を `notes/` または `proposal/` に保存する。
- **`workspace_list`**: フォルダ構成の把握（設定されている場合）。

`web_fetch_text` / `brave_web_search` が許可されていれば、公開の SEO ガイドライン・サイトの技術確認に利用してよい。

## 作業領域

- プロジェクトルートは `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, `proposal`, `decision` 等）。
- Step 1 の **`.claude/product-marketing-context.md`** は、**workspace 上の同種パス**を `file_read` で探す。無ければユーザーへのヒアリングで補う（SKILL 本文どおり）。

## references 内のコード

- [schema-examples.md](schema-examples.md) や GA4/GTM 設計書内の **JavaScript / GTM スニペットは実装・タグマネージャ向けの例示**である。Strands Agent から本番サイトへ自動デプロイされる前提ではない。

## 補完スキル

- **marketing-copy** / **ad-creative** との連携は SKILL 本文の Related Skills に従う。
