
## 12スキル用 品質判定ルール表

| スキル | 項目名 | 閾値（合格ライン） | 失格条件 |
|---|---|---|---|
| distill | 必須セクション網羅 | `要件/矛盾点/前提/未確定事項` の4見出し以上 | 見出し不足（4未満） |
| distill | 具体性 | 箇条書き5件以上 | 5件未満 |
| story-map | 階層構造 | `活動 > エピック > ストーリー` 3層が存在 | 2層以下 |
| story-map | 優先順明示 | 優先度（高/中/低 等）付き項目3件以上 | 優先度記載なし |
| software-architecture | 代替案比較 | 代替案2案以上 + 採用理由1つ以上 | 単案のみ |
| software-architecture | 非機能要件 | `性能/可用性/保守性/セキュリティ` のうち3項目以上言及 | 3項目未満 |
| decision-framework | ADR完全性 | `決定/根拠/トレードオフ/リスク` 4項目すべて存在 | 1項目でも欠落 |
| decision-framework | 追跡可能性 | 日付・版またはIDの記載あり | 識別子なし |
| diagram | 図構文妥当性 | mermaid ブロック1つ以上かつ `graph`/`flowchart` 含有 | 図ブロックなし |
| diagram | 要素対応 | 図中ノード3つ以上（本文要素と対応） | ノード3未満 |
| effective-typescript | 型安全指摘数 | `any/unsafe union/assertion` 系の具体指摘3件以上 | 指摘3件未満 |
| effective-typescript | 修正提案 | 各指摘に修正案（before/after または代替型） | 指摘のみで修正なし |
| robust-python | 堅牢性指摘数 | `例外/型/副作用/I/O境界` の具体指摘3件以上 | 指摘3件未満 |
| robust-python | 実装可能性 | 修正提案に具体コード片1つ以上 | 抽象論のみ |
| test | テスト網羅軸 | `正常/異常/境界` の3分類すべて記載 | 1分類でも欠落 |
| test | テストケース量 | ケース6件以上 | 6件未満 |
| review | JSONスキーマ | `review_id,date_utc,summary,findings,recommendations` を保持 | 必須キー欠落 |
| review | 重大指摘 | `findings` に高優先度項目1件以上 | 重大指摘ゼロ |
| data-validation | 検証ルール実行 | 必須キー・型・空値検証の3種類を実施 | 3種類未満 |
| data-validation | レポート形式 | `passed/failed/errors[]` を返す | 形式不一致 |
| agent-craft | 責務分離 | サブエージェントの責務が2つ以上明示、重複なし | 責務重複 or 1つのみ |
| agent-craft | 契約定義 | 各エージェントに入力/出力/禁止事項がある | 契約欠落 |
| skill-forge | スキル定義完全性 | `name/use when/tools/inputs/outputs` を全記載 | 欠落あり |
| skill-forge | 再利用性 | 他案件で使える汎用手順3ステップ以上 | 手順不足 |

---

## 全体判定ルール（12スキル完璧判定）

- 各スキルで上表の項目を**全て満たす**
- どれか1項目でも失格なら、そのノードで**即停止（fail-fast）**
- 最終的に `12/12 スキル = pass` のときのみ  
  **「Strands skills 検証が完璧」**

---

## 実装時にそのまま使うための判定値（推奨）

- 文字数下限: 主要成果物は 300 文字以上
- 箇条書き下限: 3〜5件（上表優先）
- JSON必須キー: 欠落1つで即 fail
- 図: mermaid 構文不成立で fail

---

## 実装フェーズ（12スキル固定）

### フェーズ1: 基盤固定
- 対象: 既存 `distill/proposal/review/rerun/recovery`
- 目的: 現行フローの安定化と fail-fast の徹底
- 完了条件:
  - `--mode full` で `summary.status=pass`（既存対象）
  - `MAX_TOKENS=8091` が全ノード固定
  - `workflow-full.log` 保存が有効

### フェーズ2: 品質判定エンジン導入
- 対象: 上記 12 スキルの品質ゲート
- 目的: ファイル有無だけでなく内容品質を機械判定
- 完了条件:
  - 本メモの「品質判定ルール表」を機械可読で評価可能
  - 1項目失格でノード即停止（fail-fast）
  - `summary` に判定結果（pass/fail, reasons）を記録

### フェーズ3: 12スキル連鎖の拡張
- 対象スキル:
  - `distill`, `story-map`, `software-architecture`, `decision-framework`, `diagram`
  - `effective-typescript`, `robust-python`, `test`, `review`, `data-validation`
  - `agent-craft`, `skill-forge`
- 目的: 12スキルを `testdata/*.md/*.ts` 入力で `skills-machine/` に連鎖出力
- 完了条件:
  - 12 スキルすべてで成果物生成
  - 各スキルが品質判定を通過

### フェーズ4: 最終判定と運用固定
- 対象: 集約判定ロジックと運用ルール
- 目的: 「完璧判定」を再現可能な運用仕様として固定
- 完了条件:
  - 最終判定が `12/12 スキル = pass` のみ
  - 失敗時に停止ノード・失格理由・再実行指示を記録
  - import は `utils` に統一、出力は日本語固定
