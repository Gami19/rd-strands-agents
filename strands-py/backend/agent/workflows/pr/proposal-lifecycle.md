---
description: >
  案件の提案書作成ライフサイクル全体を管理するワークフロー。
  pdf-convert による資料収集から distill による要件蒸留、bd-skills による提案書作成、
  drm による DRM レビュー、review による品質検証を経て、
  slide-gen / kc-slide-gen / md-to-pdf で最終成果物を出力し提出まで一気通貫で管理する。
---

# 提案書ライフサイクル ワークフロー

> 品質ゲートを通過した提案書だけが顧客の前に立つ — PDF から提出まで、妥協しない品質管理

案件の立ち上げから提案書提出までの全工程を定義する。
各工程は対応するスキルが担当し、成果物は案件ディレクトリに蓄積される。

## ワークフロー全体像

```
Phase 1: 資料収集        Phase 2: 要件蒸留       Phase 3: 提案書作成
pdf-convert              distill                 (手動 or AI)
project/10_inbox/ ← 顧客PDF project/20_notes/ ← inbox/ proposal/ ← notes/
                         project/50_decision_log/ ← ADR project/50_decision_log/ ← ADR
        │                        │                        │
        ▼                        ▼                        ▼
Phase 4: DRM レビュー    Phase 5: 品質検証        Phase 6: 提出
drm (Phase1 + Phase2)   review                   顧客へ提出
project/60_snapshots/ ← DRM1,DRM2 Review Report    project/50_decision_log/ ← 提出判断
decision_log/ ← 判定結果 ★ Critical/Major = 0
```

### 品質ゲート（Phase 間の通過条件）

| ゲート | 条件 | 不合格時のアクション |
|:---|:---|:---|
| Phase 3 → 4 | 提案書の全章が作成済み、project/20_notes の仕様が反映済み | Phase 3 に差し戻し |
| Phase 4 → 5 | DRM Phase 2 で「提案Go」または「修正Go（修正済み）」 | 差し戻し: Phase 3 再修正 → Phase 4 再実施 / No-Go: 案件中止 |
| Phase 5 → 6 | review で Critical / Major の指摘が 0 件 | 指摘箇所を修正し Phase 5 を再実施 |
| Phase 6 | 全品質ゲート通過、`project/50_decision_log/` に提出判断が記録済み | — |

### ADR 記録タイミング

設計判断が発生した時点で `project/50_decision_log/` に ADR（Architecture Decision Record）形式で記録する。

| Phase | ADR 記録タイミング | 記録内容の例 |
|:---|:---|:---|
| Phase 2 | 技術選定・方針決定時 | 技術スタック選定根拠、アーキテクチャ方針、ドメインモデル設計判断 |
| Phase 3 | 見積・体制・スケジュール確定時 | 見積算出根拠、体制構成の判断、スケジュール戦略 |
| Phase 4 | DRM 判定後 | DRM Phase 1/2 の判定結果（Go/No-Go/修正Go/差し戻し）、条件・ToDo |
| Phase 5 | review 指摘対応時 | Critical/Major 指摘への対応方針、トレードオフ判断 |
| Phase 6 | 提出判断時 | 最終提出の承認記録、残存リスクの受容判断 |

---

## 反復サイクル

Phase 4 (DRM) で差し戻しが発生した場合は Phase 3 に戻り修正。
Phase 5 (review) で Critical/Major が検出された場合も Phase 3 or 4 に差し戻す。

```
Phase 1 → Phase 2 → Phase 3 → ┌→ Phase 4 → Phase 5 ─┐ → Phase 6
                       ▲        │                      │
                       │        └── DRM 差し戻し ◀──────┘
                       │                               │
                       └── review Critical/Major ◀─────┘
```

- **Phase 3 → 4**: 全章作成後に DRM レビューへ
- **Phase 4 → 3**: DRM 差し戻し時は提案書を修正
- **Phase 5 → 3-4**: review Critical/Major 残存時は該当 Phase に差し戻し

---

## Phase 1: 資料収集（pdf-convert スキル）

**目的**: 顧客から受領した PDF/DOCX/PPTX 等を Markdown に変換し、`project/10_inbox/` に配置する。

**実行コマンド**:
```bash
python scripts/convert_to_md.py <ファイルパス> --project <案件名>
```

**成果物**: `projects/<案件名>/inbox/*.md`

**完了条件**:
- 全顧客資料が `project/10_inbox/` に Markdown 化されている
- テーブル・見出し構造が元文書と一致している

**次工程への引き渡し**:
```
「distill スキルで、<案件名> の project/10_inbox を project/20_notes に蒸留して」
```

> 💡 Phase 1 では通常 ADR 記録は不要。ただし、変換方法の選択（OCR 有無等）で判断が発生した場合は記録する。

---

## Phase 2: 要件蒸留（distill スキル）

**目的**: `project/10_inbox/` の顧客資料を分析し、構造化された仕様書を `project/20_notes/` に蒸留する。

**成果物**:
- `projects/<案件名>/notes/glossary.md` — 用語集
- `projects/<案件名>/notes/domain-model.md` — ドメインモデル
- `projects/<案件名>/notes/business-rules.md` — ビジネスルール
- `projects/<案件名>/notes/non-functional-requirements.md` — 非機能要件（該当時）
- `projects/<案件名>/notes/tech-decisions.md` — 技術選定根拠（該当時）

**完了条件**:
- 全 project/10_inbox 資料が project/20_notes に反映済み
- トレーサビリティマトリクスで要件の追跡が可能

**ADR 記録**: 技術選定・アーキテクチャ方針・ドメインモデル設計などの判断が発生した場合、`project/50_decision_log/` に ADR 形式で記録する。

```
# ADR ファイル命名規則
project/50_decision_log/ADR-NNNN-<判断概要>.md

# 例
project/50_decision_log/ADR-0001-技術スタック選定-Azure-PaaS.md
project/50_decision_log/ADR-0002-認証方式-Entra-ID.md
```

---

## Phase 3: 提案書作成（bd-skills スキル）

**目的**: `project/20_notes/` の構造化仕様に基づき、提案書を `proposal/` に作成する。

### 使用スキル

| スキル | 役割 |
|:---|:---|
| **bd-skills** | 提案書の章構成設計、本文作成、見積・体制・スケジュール |
| **diagram** | As-Is/To-Be 構成図、アーキテクチャ図 |
| **marketing-copy** | エグゼクティブサマリー、差別化コピーの磨き上げ |
| **data-validation** | 見積金額・工数・ROI の数値整合性検証 |

### 成果物

| 成果物 | 格納先 |
|:---|:---|
| 提案書（章立て Markdown） | `projects/<案件名>/proposal/*.md` |
| 構成図（draw.io） | `projects/<案件名>/proposal/diagrams/` |
| ADR（見積・体制判断） | `projects/<案件名>/decision_log/` |

### 完了チェックリスト

- [ ] RFP の全要件に対応する章が存在する
- [ ] project/20_notes の仕様が正確に反映されている
- [ ] 見積金額・工数・スケジュールが記載されている
- [ ] 構成図が提案書に埋め込まれている
- [ ] data-validation で見積数値の整合性を検証済み

### Agent Teams（並行実行パターン）

```
「Agent Team で以下を並行実行して：
  - Teammate 1: bd-skills で提案書の章構成と本文を作成
  - Teammate 2: diagram で As-Is/To-Be 構成図を作成
  - Teammate 3: marketing-copy でエグゼクティブサマリーを磨き上げ」
```

**ADR 記録**: 見積算出根拠、体制構成の判断、スケジュール戦略などを `project/50_decision_log/` に記録する。

```
# 例
project/50_decision_log/ADR-0003-見積算出根拠-160人日.md
project/50_decision_log/ADR-0004-体制構成-PM1-SE3-構成.md
```

---

## Phase 4: DRM レビュー（drm スキル）★ 提案書作成後に必ず実施

**目的**: 提案書の初版完成後、DRM（Deal Review Meeting）のアジェンダ・台本を生成し、`project/60_snapshots/` に保存する。

CRITICAL: Phase 3（提案書作成）が完了した時点で、DRM Phase 1 と DRM Phase 2 の両方を生成すること。

### Step 4-1: DRM Phase 1（提案着手の承認 — Go/No-Go）

提案を進めるべきか否かの判断材料を整理する。

**実行指示**:
```
「drm スキルで、<案件名> のフェーズ1（提案着手の承認）アジェンダを生成して。
 出力先は projects/<案件名>/snapshots/DRM1-<案件名>.md にしてください。」
```

**成果物**: `projects/<案件名>/snapshots/DRM1-<案件名>.md`

**台本に含まれる内容**:
- 案件サマリ（背景・要望・金額・期限）
- BANT 確認・リスク・体制案
- 審議: ライセンス、提案実行体制、アクションプラン・スケジュール
- 判定: Go / No-Go / 条件付きGo
- ToDo（担当・期限）

**入力情報（drm スキルに提供すべき内容）**:
- `projects/<案件名>/notes/` の仕様概要
- `projects/<案件名>/proposal/` の見積・体制・スケジュール
- 顧客の BANT 情報（判明している範囲）

### Step 4-2: DRM Phase 2（提案書提出前レビュー）★ 最重要

「このまま出して勝てるか？」を全員で確認するための台本を生成する。

**実行指示**:
```
「drm スキルで、<案件名> のフェーズ2（提案書提出前レビュー）アジェンダを生成して。
 出力先は projects/<案件名>/snapshots/DRM2-<案件名>.md にしてください。」
```

**成果物**: `projects/<案件名>/snapshots/DRM2-<案件名>.md`

**台本に含まれる内容（4審議構成）**:
1. 審議1: バリューチェック（価値筋・ライセンス・運用保守の訴求）
2. 審議2: 原価レビュー（粗利・バッファ妥当性）
3. 審議3: リスク・競合・検証判断
4. 審議4: 総合判断（提案Go / 修正Go / 差し戻し）
5. 議事録メモ欄

**入力情報（drm スキルに提供すべき内容）**:
- `projects/<案件名>/proposal/` の提案書全体
- 想定原価の内訳（人件費・外注費・ライセンス費）
- 想定粗利率、守るべき粗利ライン
- 競合情報（判明している範囲）
- 事前検証の状況

### DRM 完了後のアクション

| DRM 判定結果 | 次のアクション | ADR 記録 |
|:---|:---|:---|
| **Go** | Phase 5（review）に進む | 判定結果・条件を記録 |
| **修正Go** | 指摘箇所を修正し、Phase 5（review）に進む | 判定結果・修正箇所・条件を記録 |
| **差し戻し** | 指摘箇所を大幅修正し、Phase 4 を再実施 | 判定結果・差し戻し理由を記録 |
| **No-Go** | 案件を中止 | 判定結果・中止理由を記録 |

**ADR 記録**: DRM の判定結果は必ず `project/50_decision_log/` に記録する。

```
# 例
decision_log/ADR-0005-DRM1-Go判定-条件付き.md
decision_log/ADR-0006-DRM2-修正Go-粗利率見直し.md
```

---

## Phase 5: 品質検証（review スキル）★ 品質ゲート

**目的**: DRM を通過した提案書をレッドチームレビューで最終検証する。

**前提条件（品質ゲート）**: Phase 4 の DRM Phase 2 で「提案Go」または「修正Go（修正済み）」であること。

**実行指示**:
```
# 提案書レビュー（必須）
「review スキルで、<案件名> の提案書をレビューして」

# 技術仕様レビュー（技術提案を含む場合）
「review スキルで、<案件名> のソースコードを project/20_notes との整合性の観点からレビューして」
```

**成果物**: Review Report（`projects/<案件名>/proposal/` または指定の場所に出力）

**検証観点（提案書レビュー）**:
- A-1: RFP 要件カバレッジ — 全要件への対応漏れがないか
- A-2: 章間整合性 — 章をまたぐ記述の矛盾がないか
- A-3: 見積精度と妥当性 — 工数・金額・スケジュールの整合性
- A-4: 可読性と説得力 — 顧客視点での説得力

**検証観点（技術仕様レビュー、該当時）**:
- B-1: project/20_notes との仕様乖離
- B-2: 会計整合性（数値・計算の正確性）
- B-3: 境界値攻撃（エッジケースの考慮）
- B-4: セキュリティ
- B-5: パフォーマンス
- B-6: テストカバレッジ

**完了条件（品質ゲート）**:
- Critical / Major の指摘が **0 件**
- DRM での修正指示が全て反映済み
- ★ 上記を満たさない場合、指摘箇所を修正し Phase 5 を再実施する

### Agent Teams（並行実行パターン）

```
「Agent Team で以下を並行実行して：
  - Teammate 1: review で提案書を 4 軸レビュー
  - Teammate 2: data-validation で全数値・見積を検証」
```

**ADR 記録**: Critical/Major 指摘への対応方針にトレードオフ判断が伴う場合、`project/50_decision_log/` に記録する。

```
# 例
project/50_decision_log/ADR-0007-review指摘-A3-見積工数修正.md
```

---

## Phase 6: 提出

**前提条件（全品質ゲート通過）**:
- DRM Phase 2 で「提案Go」または「修正Go（修正済み）」
- review で Critical / Major が **0 件**
- `project/50_decision_log/` に全 Phase の判断が記録済み

**ADR 記録**: 提出判断を `project/50_decision_log/` に記録する（必須）。

```
# 例
project/50_decision_log/ADR-0008-提出判断-Go-残存リスク受容.md
```

---

## Agent Teams による並行実行

Phase 4 の DRM1 と DRM2 は並行生成が可能:

```
「Agent Team で以下を並行実行して：
  - Teammate 1: drm スキルで <案件名> のフェーズ1アジェンダを project/60_snapshots/ に生成
  - Teammate 2: drm スキルで <案件名> のフェーズ2アジェンダを project/60_snapshots/ に生成」
```

---

## ディレクトリと成果物マッピング

```
projects/<案件名>/
├── inbox/          ← Phase 1: 顧客資料（Markdown化済み）
├── notes/          ← Phase 2: 構造化仕様（SSoT）
├── proposal/       ← Phase 3: 提案書
├── snapshots/      ← Phase 4: DRM アジェンダ・台本
│   ├── DRM1-<案件名>.md   ← DRM Phase 1 Go/No-Go
│   └── DRM2-<案件名>.md   ← DRM Phase 2 提出前レビュー
├── decision_log/   ← Phase 2〜6: ADR（設計判断）・DRM判定結果・提出判断
│   ├── ADR-0001-*.md      ← 技術選定・方針判断
│   ├── ADR-NNNN-DRM*.md   ← DRM 判定結果
│   └── ADR-NNNN-提出判断-*.md ← 最終提出承認
└── references/     ← 外部参照

> **Note**: プラットフォーム標準では知識関連ディレクトリは `project/` プレフィックスを使用する（`project/10_inbox/`、`project/20_notes/`、`project/50_decision_log/` 等）。`projects/<案件名>/` 配下で管理する場合も、各サブディレクトリの役割は同じ。
```

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| Phase 1 で PDF 変換が文字化けする | 非埋め込みフォント PDF | OCR モードで再変換、または手動修正 |
| Phase 2 で蒸留結果が浅い | project/10_inbox 資料の読み込みが不十分 | distill に複数パスを指示。チャンク分割で蒸留 |
| Phase 2 で用語が統一されない | 用語集未作成 | glossary.md を先に作成し、蒸留時に用語統一を指示 |
| Phase 3 で提案書の章立てが決まらない | 顧客 RFP の構造が不明確 | RFP の評価基準を分析し、配点に応じた章構成を設計 |
| Phase 3 で見積が収束しない | 前提条件が未確定 | 前提条件を ADR に明文化し、条件付き見積として提示 |
| Phase 4 DRM1 で No-Go 判定 | 案件リスクが高い | 判定理由を ADR に記録。条件付き再検討の可否を確認 |
| Phase 4 DRM2 で差し戻しが繰り返される | 提案の価値筋が弱い | Phase 2 に戻り課題分析と差別化を再実施 |
| Phase 4 で DRM1 と DRM2 の判断が矛盾 | DRM1 の条件が DRM2 で未反映 | DRM1 の条件を提案書に反映してから DRM2 を再実施 |
| Phase 5 で Critical 指摘が大量 | 章間の整合性不足 | エグゼクティブサマリーから逆算し、各章の記述を統一 |
| Phase 5 で review と DRM の指摘が矛盾 | 観点の違い | DRM は BD 戦略観点、review は品質観点。ADR で判断を明文化 |
| Phase 5 → 3 の差し戻しが繰り返される | 要件が不安定 | Phase 2 に戻り蒸留をやり直し、トレーサビリティで追跡 |
| 全体の進行が遅れる | 依存関係の把握不足 | Phase 1-2 を最優先で完了し、以降を並行実行 |

---

## スキル発動マトリクス（全フェーズ × 全スキル）

| スキル | Ph.1 | Ph.2 | Ph.3 | Ph.4 | Ph.5 | Ph.6 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **pdf-convert** | **主** | - | - | - | - | - |
| **distill** | - | **主** | - | - | - | - |
| **bd-skills** | - | - | **主** | - | - | - |
| **diagram** | - | - | **補** | - | - | - |
| **marketing-copy** | - | - | **補** | - | - | - |
| **data-validation** | - | **補** | **補** | - | **補** | - |
| **drm** | - | - | - | **主** | - | - |
| **review** | - | - | - | - | **主** | - |
| **slide-gen** / **kc-slide-gen** | - | - | - | - | - | **補** |
| **md-to-pdf** | - | - | - | - | - | **補** |

**凡例**: **主** = フェーズの主要スキル、**補** = 補助的に使用、- = 不使用

---

## スキル間連携図

```
Phase 1: 資料収集
┌────────────────────────────────┐
│ pdf-convert → project/10_inbox/ に蓄積 │
└───────────────┬────────────────┘
                │
                ▼
Phase 2: 要件蒸留
┌────────────────────────────────┐
│ distill         → 用語集/要件  │
│ data-validation → 数値検証     │
└───────────────┬────────────────┘
                │
                ▼
Phase 3: 提案書作成
┌────────────────────────────────┐
│ bd-skills      → 章構成/本文   │
│ diagram        → 構成図        │
│ marketing-copy → コピー磨き    │
│ data-validation → 見積検証     │
└───────────────┬────────────────┘
                │
                ▼
Phase 4: DRM レビュー
┌────────────────────────────────┐
│ drm (DRM1) → Go/No-Go         │
│ drm (DRM2) → 提出前レビュー   │
│ → 差し戻し時は Phase 3 に戻る  │
└───────────────┬────────────────┘
                │
                ▼
Phase 5: 品質検証
┌────────────────────────────────┐
│ review          → 4軸レビュー  │
│ data-validation → 最終数値検証 │
│ → Critical/Major 残存時は差戻し│
└───────────────┬────────────────┘
                │
                ▼
Phase 6: 提出・納品
┌────────────────────────────────┐
│ slide-gen / kc-slide-gen → PPTX│
│ md-to-pdf                → PDF │
└────────────────────────────────┘
```

---

## クイックスタートパターン

### パターン A: RFP ベースの標準提案

```
1. 「この RFP を project/10_inbox に取り込んで」   → pdf-convert
2. 「project/10_inbox の資料を project/20_notes に蒸留して」 → distill
3. 「提案書を作って」                            → bd-skills
4. 「構成図を描いて」                            → diagram
5. 「DRM アジェンダを作って」                    → drm
6. 「提案書をレビューして」                      → review
7. 「提案書を PPTX にして」                      → kc-slide-gen
```

### パターン B: 口頭相談からの提案

```
1. 「ヒアリング結果をもとに要件を構造化して」     → distill
2. 「提案書を作って」                            → bd-skills
3. 「コピーを改善して」                          → marketing-copy
4. 「レビューして」                              → review
5. 「PDF にして」                                → md-to-pdf
```

### パターン C: コスト最適化の簡易提案

```
1. 「コスト最適化の提案書を作って」               → bd-skills
2. 「ROI の数値を検証して」                       → data-validation
3. 「レビューして」                              → review
4. 「スライドにして」                            → slide-gen
```

### パターン D: 技術提案（アーキテクチャ設計含む）

```
1. 「RFP を変換して project/20_notes に蒸留して」    → pdf-convert + distill
2. 「データアーキテクチャを設計して」              → data-arch
3. 「構成図を描いて」                            → diagram
4. 「提案書を作って」                            → bd-skills
5. 「DRM を準備して」                            → drm
6. 「レビューして数値を検証して」                 → review + data-validation
7. 「KC テンプレートで PPTX にして」              → kc-slide-gen
```

---

## 関連ワークフロー

| ワークフロー | 関係性 |
|:---|:---|
| [bd-skills-workflow.md](bd-skills-workflow.md) | BD ワークフローの Phase 3-4 で本ワークフローを使用 |
| [engineering-workflow.md](engineering-workflow.md) | 技術提案はエンジニアリング Phase 1-2 のアーキテクチャ設計と連動 |
| [convert-pdf.md](convert-pdf.md) | Phase 1 の PDF 変換手順の詳細 |
| [marketing-workflow.md](marketing-workflow.md) | 提案書にマーケティング戦略セクションを含める場合 |
