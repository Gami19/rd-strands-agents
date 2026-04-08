---
name: project-ops
description: >
  プロジェクトの運用・戦術レベルのフロー最適化を支援する。チーム認知負荷の測定・最適化、
  依存関係の分析・解消、制約理論（TOC）によるボトルネック管理、DORA メトリクスの改善、
  Dynamic Reteaming による段階的チーム移行を実践的にガイドする。
  Use when user says「プロジェクトの進め方を設計して」「チームの認知負荷を最適化したい」
  「依存関係を分析して」「DORAメトリクスを改善したい」「フローを最適化して」
  「ボトルネックを特定して」「チーム再編成を計画したい」「スプリントの流れを改善したい」
  「ハンドオフを減らしたい」「デリバリパフォーマンスを上げたい」。
  Do NOT use for: Wardley Map の戦略策定やDDD Bounded Context 設計（→ flow-architecture）、
  個別のデータアーキテクチャ設計（→ data-arch）、単純なタスク管理やチケット運用。
metadata:
  author: KC-Prop-Foundry
  version: 1.1.0
  category: development
  pattern: "sequential"
  based-on: "Architecture for Flow (Susanne Kaiser, Pearson Addison-Wesley 2025) — Ch.5-11"
---

# Skill: Project Operations（プロジェクト運用・フロー最適化）

> **戦略は flow-architecture が描く。project-ops はその戦略を現場で実行し、日々のフローを計測・改善する**

## strands-py / Strands Agent での利用

依存分析・DORA・再編成計画などは **`file_read` / `file_write`** とプロジェクト workspace（`notes` / `proposal` 等）を正とする。詳細は [references/strands-py-runtime.md](references/strands-py-runtime.md) を参照。

## Instructions

### ワークフロー内の位置

```
flow-architecture → [project-ops] → 実行・改善 → review → drm
  (戦略設計)        (運用・戦術)     (継続的改善)
                        ↓
                   ・依存関係分析レポート
                   ・認知負荷評価マトリクス
                   ・制約分析 & TOC 改善計画
                   ・DORA メトリクス改善ロードマップ
                   ・チーム再編成計画（Dynamic Reteaming）
                   ・フロー最適化アクションプラン
```

### 入力

| 入力 | 説明 | 例 |
|:---|:---|:---|
| 現在のチーム構成 | チーム名・人数・責任・インタラクション | FE 5名、BE 8名、Infra 3名 の機能サイロ |
| 変更フローの状況 | デリバリの流れと課題 | 「リリースに3週間かかる」「QA がボトルネック」 |
| DORA メトリクス（あれば） | 現在のパフォーマンス指標 | 月1デプロイ、Lead Time 2週間 |
| アーキテクチャ情報 | システム構造・技術的負債 | モノリス、共有DB、テスト不足 |

### 出力

| 出力 | 形式 | 説明 |
|:---|:---|:---|
| 依存関係分析レポート | Markdown テーブル | 3種の依存（Architecture/Expertise/Activity）の可視化 |
| 認知負荷評価マトリクス | Markdown テーブル | チーム別の負荷レベルと最適化提案 |
| 制約分析 & TOC 改善計画 | Markdown | ボトルネック特定と5ステップ改善策 |
| DORA メトリクス改善ロードマップ | Markdown テーブル | 現状→目標→アクションの対応表 |
| チーム再編成計画 | Markdown | Dynamic Reteaming パターンを使った移行ステップ |
| フロー最適化アクションプラン | Markdown | 優先順位付きの改善アクション一覧 |

---

## Step 1: 現状アセスメント（As-Is Teams & Flow）

チーム構造、依存関係、フロー阻害要因を調査し、現状の全体像を把握する。

### 1a. チーム構造の記述

以下の情報を整理する:

| 観点 | 確認内容 |
|:---|:---|
| チーム名・人数 | 各チームの名前とメンバー数 |
| 責任範囲 | 各チームが所有するシステム領域 |
| チームタイプ | 機能サイロか / SA / Platform / Enabling / Complicated-subsystem か |
| インタラクション | チーム間の連携方法（PR、チケット、定例等） |
| プラクティス | 現在の作業方法（Scrum、Kanban 等） |

### 1b. フロー阻害・促進要因の収集

チームインタビューの4象限フレームワーク:

```
┌────────────────────┬────────────────────┐
│ 🔴 フローを阻害     │ 🟢 フローを支える     │
│  するもの            │  もの                │
│  (Blockers)         │  (Enablers)          │
├────────────────────┼────────────────────┤
│ ↓ 最小化すべき       │ ↓ 保持すべき          │
│  (Minimize)         │  (Preserve)          │
└────────────────────┴────────────────────┘
```

### 1c. 変更ストリームの特定

- ユーザーニーズから顧客駆動の変更ストリームを導出
- ストリームタイプ: タスク / ロール / 活動 / 地理 / 顧客セグメント
- 最も価値が高く、変更頻度の高いストリームを優先

### 1d. DORA メトリクスの現状把握

| メトリクス | 現在値 | レベル判定 |
|:---|:---|:---|
| Deployment Frequency | _____ | Elite / High / Medium / Low |
| Lead Time for Changes | _____ | Elite / High / Medium / Low |
| Mean Time to Restore | _____ | Elite / High / Medium / Low |
| Change Failure Rate | _____ | Elite / High / Medium / Low |

レベル判定基準:

| レベル | Deploy Freq | Lead Time | MTTR | CFR |
|:---|:---|:---|:---|:---|
| Elite | On-demand | < 1h | < 1h | 0-15% |
| High | Daily-Weekly | 1d-1w | < 1d | 16-30% |
| Medium | Weekly-Monthly | 1w-1m | < 1w | 16-30% |
| Low | < Monthly | 1m-6m | > 6m | > 30% |

**チェックリスト**:
- [ ] 全チームの構造・責任・人数が記述されている
- [ ] フロー阻害要因と促進要因が収集されている
- [ ] 主要な変更ストリームが特定されている
- [ ] DORA メトリクスの現状が把握されている（推定でも可）

---

## Step 2: 依存関係分析（3 Types of Dependencies）

チーム間・システム間の依存関係を3分類で分析し、フローを阻害する構造を可視化する。

### 2a. Architecture Dependencies の分析

以下を確認:
- 1つのコンポーネント変更が他のどこに波及するか
- 関連する振る舞いがシステム全体に散在していないか
- 変更に何チームの調整が必要か

**アーキテクチャ結合度マトリクス**:

| 変更元 | 影響先 | 結合度（高/中/低） | 根本原因 |
|:---|:---|:---|:---|
| (記入) | (記入) | (記入) | (記入) |

### 2b. Expertise Dependencies の分析

- 「この人/チームがいないと進められない」知識の依存を特定
- Bus Factor（その人がいなくなったらプロジェクトが止まるか）を評価
- 知識のサイロ化ポイントを可視化

### 2c. Activity Dependencies の分析

- チーム間のハンドオフを列挙
- 各ハンドオフの待ち時間を推定
- E2E フロー所有権の欠如を特定

**依存関係サマリテーブル**:

| 依存元チーム | 依存先チーム | 依存タイプ | 深刻度 | 解消策候補 |
|:---|:---|:---|:---|:---|
| (記入) | (記入) | Arch / Exp / Act | 高/中/低 | (記入) |

**チェックリスト**:
- [ ] Architecture Dependencies が分析されている
- [ ] Expertise Dependencies が特定されている
- [ ] Activity Dependencies（ハンドオフ）が列挙されている
- [ ] 各依存の深刻度が評価されている
- [ ] 解消策の候補が検討されている

---

## Step 3: 認知負荷の最適化

各チームの認知負荷を評価し、最適化のための施策を設計する。

### 3a. 認知負荷の3モダリティ評価

チームごとに3つの認知負荷を評価:

| チーム | Intrinsic Load（本質的難しさ） | Extraneous Load（提示方法の問題） | Germane Load（学習負荷） | 総合評価 |
|:---|:---|:---|:---|:---|
| (記入) | 高/中/低 | 高/中/低 | 高/中/低 | 超過/適正/余裕 |

### 3b. Evolution Stage ベースのヒューリスティクス適用

所有するドメイン/コンポーネントの進化段階に基づく負荷上限:

| Evolution Stage | Cynefin Domain | 推奨 BC 数/team | Practice Type |
|:---|:---|:---|:---|
| Genesis | Chaotic/Complex | 1 BC | Novel |
| Custom-Built | Complex | 1-2 BCs | Emergent |
| Product (+rental) | Complicated | 2-3 BCs | Good |
| Commodity (+utility) | Clear | 3+ BCs | Best |

**注意**: チームに経験がなければ、Commodity 段階のコンポーネントでも Complex ドメインになりうる。Cynefin で補完判定する。

### 3c. 最適化施策の設計

| 負荷タイプ | 改善策 | 担当 |
|:---|:---|:---|
| Intrinsic が高すぎる | BC の分割、Complicated-subsystem Team の組成 | アーキテクト |
| Extraneous が高い | ドキュメント整備、Platform Team の TVP 提供 | Platform Team |
| Germane が高い | Enabling Team のコーチング、ペアプロ、Software Teaming | Enabling Team |
| 所有 BC 数が多すぎる | チーム分割（Grow and Split）、BC の再割り当て | マネージャー |

**チェックリスト**:
- [ ] 各チームの認知負荷が3モダリティで評価されている
- [ ] Evolution Stage ヒューリスティクスが適用されている
- [ ] Cynefin 補完判定が必要なケースが特定されている
- [ ] 具体的な最適化施策が提案されている

---

## Step 4: 制約の特定と TOC 適用

Theory of Constraints の5ステップを適用し、システム全体のフローを制約しているボトルネックを特定・管理する。

### 4a. Value Stream Mapping（VSM）

主要な変更ストリームについて VSM を作成:

```
[Process Step 1] → [Process Step 2] → [Process Step 3] → [Delivered]
  CT: ___         CT: ___             CT: ___
  WT: ___         WT: ___             WT: ___
  LT: ___         LT: ___             LT: ___
  C/A: ___%       C/A: ___%           C/A: ___%

Total VA (Cycle Time): ___
Total NVA (Wait Time): ___
Total Lead Time: ___
Flow Efficiency: VA / LT × 100 = ___%
```

CT = Cycle Time（作業時間）, WT = Wait Time（待ち時間）, LT = Lead Time, C/A = Complete & Accurate %

### 4b. 制約の特定（TOC Step 1: Identify）

特定の手がかり:
- **最も長いキュー**: ワークが溜まっている場所 → その直後のステップが制約
- **最も長い待ち時間**: NVA が突出しているステップ
- **アイドルリソース**: リソースが待機状態 → その前段が制約
- **低い C/A%**: 手戻りが多いステップ

### 4c. TOC 5 Steps の適用

| Step | アクション | 具体策 |
|:---|:---|:---|
| 1. Identify | 制約を特定 | VSM + キュー分析の結果: ________ |
| 2. Exploit | 制約の NVA を排除 | 制約が最優先タスクに集中できるようにする |
| 3. Subordinate | 非制約のペースを調整 | 制約より速くワークを流入させない（WIP 制限等） |
| 4. Elevate | 制約の能力を拡大 | 人員追加 / スキルアップ / ツール導入 / プロセス改善 |
| 5. Repeat | 次の制約を探す | 制約が解消されたら VSM を再実施 |

**チェックリスト**:
- [ ] 主要な変更ストリームの VSM が作成されている
- [ ] Flow Efficiency（VA/LT）が計算されている
- [ ] ボトルネックが特定されている
- [ ] TOC 5 Steps の改善策が具体的に記述されている
- [ ] 「ボトルネック以外の改善は幻想」の原則が遵守されている

---

## Step 5: チームトポロジー設計（実践的チーム編成）

分析結果に基づき、実際のチーム編成を Team Topologies のパターンで設計する。

### 5a. チームタイプの割り当て

| 領域/コンポーネント | 推奨チームタイプ | 根拠 |
|:---|:---|:---|
| 顧客価値の変更ストリーム | Stream-aligned Team | E2E の価値提供に整合 |
| インフラ・基盤サービス | Platform Team | セルフサービスで SA チームの負荷軽減 |
| スキルギャップ領域 | Enabling Team | 内部コーチングで自律性向上 |
| 高度専門知識領域 | Complicated-subsystem Team | 専門知識の集約で SA チームの負荷軽減 |

### 5b. チームサイズと信頼境界

Dunbar's Number に基づく設計:
- **5人**: 親密な関係（最小チームサイズ）
- **9人**: 深い信頼の上限（推奨最大チームサイズ）
- **15人**: 深い信頼の拡張境界
- **50人**: 相互信頼の限界（部門規模）

Brooks's Law: チームに人を追加するとコミュニケーションパスが増大し、一時的に生産性が低下する。

### 5c. インタラクションモードの設計

| チーム間 | 初期モード | 進化先 | トリガー |
|:---|:---|:---|:---|
| Platform → SA | Collaboration | XaaS | SA チームが自律的にタスク完遂可能になったら |
| Enabling → SA | Facilitating | 解消 | SA チームがスキルを習得したら |
| SA → SA | Collaboration | Separate Ways or API | 共同探索が完了したら |

### 5d. Platform Team の TVP（Thinnest Viable Platform）設計

TVP の段階的拡張:
1. **Phase 0**: ドキュメント、標準、チェックリスト、ベストプラクティス
2. **Phase 1**: テンプレート、プリコンフィグ済み設定
3. **Phase 2**: セルフサービス API、CLI ツール
4. **Phase 3**: デジタルプラットフォーム（フル自動化）

**チェックリスト**:
- [ ] 全チームにチームタイプが割り当てられている
- [ ] チームサイズが 5-9人の範囲に収まっている
- [ ] チーム間インタラクションモードが定義されている
- [ ] インタラクションの進化パスが計画されている
- [ ] Platform Team の TVP が定義されている

---

## Step 6: DORA メトリクス改善計画

現在の DORA レベルから目標レベルへの改善ロードマップを策定する。

### 6a. 改善ロードマップ

| メトリクス | 現在 | 目標（3M） | 目標（6M） | 主要アクション |
|:---|:---|:---|:---|:---|
| Deployment Frequency | _____ | _____ | _____ | (記入) |
| Lead Time for Changes | _____ | _____ | _____ | (記入) |
| MTTR | _____ | _____ | _____ | (記入) |
| Change Failure Rate | _____ | _____ | _____ | (記入) |

### 6b. メトリクス別改善パターン

**Deployment Frequency を上げるには**:
- CI/CD パイプラインの構築・改善
- Feature Flag による段階的リリース
- 機能サイロ → SA チーム化（ハンドオフ削減）
- Platform Team によるセルフサービスデプロイ基盤

**Lead Time を短縮するには**:
- ハンドオフの削減（SA チーム化）
- レビュー待ち時間の短縮（ペアプロ、Software Teaming）
- 自動テストによるフィードバック高速化
- WIP 制限によるマルチタスク抑制

**MTTR を短縮するには**:
- Observability の強化（ログ、メトリクス、トレーシング）
- Runbook の整備と自動化
- インシデント対応の訓練（Game Day）
- 小さなデプロイ単位（変更の局所化）

**Change Failure Rate を下げるには**:
- 自動テスト（ユニット + 統合 + E2E）の拡充
- コードレビューの品質向上
- カナリアリリース / Blue-Green デプロイ
- テスト in Production（Observability + Feature Flag）

### 6c. 組織文化の評価

Westrum 文化モデルでチームの文化を評価:

| 指標 | 病理的 | 官僚的 | 生成的 |
|:---|:---|:---|:---|
| 情報の流れ | 隠蔽 | ルール経由 | 積極的共有 |
| 失敗への反応 | 隠蔽・処罰 | 手続き的対応 | 学習・改善 |
| 新しい試み | 潰される | 問題視 | 歓迎・実装 |
| 責任 | 回避 | 部門内限定 | 共有 |

**チェックリスト**:
- [ ] DORA 改善ロードマップが作成されている
- [ ] 各メトリクスに具体的なアクションが紐づいている
- [ ] 組織文化の評価が行われている
- [ ] 短期（3M）と中期（6M）の目標が設定されている

---

## Step 7: To-Be 設計 & 移行ロードマップ

全ステップの分析結果を統合し、移行計画を策定する。

### 7a. Dynamic Reteaming パターンの適用

| Phase | Reteaming パターン | 内容 |
|:---|:---|:---|
| Phase 1 | **Isolation** | 最初の SA/Platform チームを組成。既存チームからボランティアを抽出 |
| Phase 2 | **Merging** | 移行完了した旧チームメンバーを新チームに統合 |
| Phase 3 | **Grow and Split** | 大きくなったチームを分割 |
| 継続 | **Switching** | 年1-2回のチーム間ローテーションで知識共有と人材保持 |

### 7b. Calibration Session の計画

新チーム組成時に必ず実施:
- ミッションの確認と合意
- 期待成果の定義
- 優先順位の設定
- ワークフロー・作業規約の合意
- チームメンバーの役割と強みの共有

### 7c. インクリメンタル移行計画

```
Phase 1: Foundation（基盤整備）— 4-6 weeks
  - As-Is 評価の完了と共有
  - 最初の Platform Team 組成（Isolation）
  - 効率ギャップの解消開始（Replatforming 等）
  - DORA メトリクスのベースライン確立

Phase 2: First Stream（最初の SA チーム）— 6-8 weeks
  - 最初の SA Team 組成（Isolation）
  - 最初の BC 抽出（Generic から Quick Win）
  - Platform → SA の Collaboration 開始
  - Modular Monolith First 戦略の適用

Phase 3: Expand（拡張）— 8-12 weeks
  - 次の SA Team を段階的に組成
  - Platform → XaaS への移行
  - Enabling Team の検討
  - DORA メトリクスの改善確認

Phase 4: Optimize（最適化）— 継続
  - フロー指標の継続的計測
  - ボトルネックの再評価（TOC 繰り返し）
  - チームインタラクションの進化
  - 組織文化の改善（生成的文化へ）
  - Learning Organization の規律の実践
```

### 7d. フロー最適化アクションプラン（統合）

全ステップの結果を優先順位付きのアクションリストに統合:

| # | アクション | カテゴリ | 期待効果 | 優先度 | 担当 | Phase |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | (記入) | 依存/認知/制約/DORA | (記入) | P1/P2/P3 | (記入) | 1/2/3/4 |

### 7e. プロジェクト運用 Slop 防止チェック（Distributional Convergence 対策）

LLM が生成するプロジェクト運用改善提案は、DevOps ブログや DORA レポートで頻出する「標準的な改善プレイブック」に収束しやすい。組織固有のチーム文化・技術的負債の質・ビジネス制約を反映しない「汎用改善計画」は、教科書的には正しくても現場で実行不能になる。

| # | プロジェクト運用 Slop パターン | 検出方法 | 対策 |
|:---|:---|:---|:---|
| PO-1 | **DORA 改善プレイブック直写し** | DORA メトリクス改善提案が「CI/CD 導入→自動テスト→Feature Flag→モニタリング」の同一ステップか確認 | 組織の現状レベルと制約に応じた改善順序を設計する。テストが皆無なら CI/CD より先にテスト基盤、デプロイが手動なら Feature Flag より先に自動化。TOC で特定した制約から着手 |
| PO-2 | **認知負荷スコアの均一化** | 全チームの認知負荷評価が似たようなスコア（すべて「中」等）になっていないか確認 | チーム固有の状況を深掘りする。所有する BC の Evolution Stage、チームメンバーの経験年数分布、技術スタック固有の複雑度、組織内政治的負荷（ステークホルダー調整コスト）を個別に評価 |
| PO-3 | **VSM ボトルネックの定型化** | Value Stream Mapping のボトルネックがすべて「コードレビュー待ち」「QA 待ち」「デプロイ承認待ち」の同一箇所か確認 | 実際のフローデータ（チケット滞留時間、PR マージまでの時間分布）を分析する。ボトルネックは「手戻り」「要件不明確による作業中断」「共有 DB スキーマ変更の調整」等、組織固有の箇所にある場合が多い |
| PO-4 | **Cross-functional チーム一択** | チーム構造の改善提案がすべて「機能サイロ→クロスファンクショナルチーム」の同一パターンか確認 | Team Topologies の 4 チームタイプ（SA/Platform/Enabling/Complicated-subsystem）を文脈に応じて使い分ける。全チームを SA 化するのではなく、Complicated-subsystem Team で専門知識を集約する選択肢も評価 |
| PO-5 | **WIP 制限の画一適用** | フローメトリクスの改善提案がすべて「WIP 制限を導入する」の同一施策か確認 | WIP 制限は手段であり目的ではない。制約の根本原因（スキル不足 / アーキテクチャ結合 / 承認プロセス過多 / 割り込み文化）を特定し、それに応じた施策を選定する。WIP 制限が効くのは制約が「作業の並列度」にある場合のみ |
| PO-6 | **Kaizen テンプレートの反復** | 改善サイクルがすべて「振り返り→課題特定→改善アクション→効果測定」の同一テンプレートか確認 | 改善の性質に応じたアプローチを選ぶ。プロセス改善には TOC 5 Steps、チーム構造改善には Dynamic Reteaming、技術的改善には Architectural ADR、文化改善には Westrum モデルの段階的移行。「振り返り」の形式も、KPT / Start-Stop-Continue / Sailboat 等から文脈に応じて選定 |

> **核心原則**: **改善は地図ではなくコンパスである** — 汎用的なロードマップを適用するのではなく、現場の制約とフローデータに基づいて方向を定める。「別の組織のフロー改善計画にそのまま差し替えても違和感がないか？」→ 違和感がないなら Project Ops Slop である。

**チェックリスト**:
- [ ] Dynamic Reteaming パターンが適用されている
- [ ] Calibration Session が計画されている
- [ ] インクリメンタル移行計画が Phase 分けされている
- [ ] 各 Phase の成功基準が定義されている
- [ ] フロー最適化アクションプランが統合されている
- [ ] As-Is で特定した阻害要因の解消が計画に含まれている
- [ ] 「Big-bang 再編成を避ける」原則が遵守されている
- [ ] プロジェクト運用 Slop チェック（PO-1〜PO-6）に 2 つ以上該当しない
- [ ] 出力がドメイン固有の要素を含み、汎用テンプレートに見えない

---

## Examples

### Example 1: 機能サイロチームのフロー最適化

```
「FE/BE/Infra のサイロ構造でデリバリが遅い。改善したい」

→ Step 1 で現状アセスメント: 3チーム（FE 6名、BE 8名、Infra 3名）、
  リリースに3週間、月1デプロイ
→ Step 2 で依存分析: Activity Dependencies が深刻（FE→BE→Infra のハンドオフ連鎖）
→ Step 3 で認知負荷評価: BE チームが12サービス所有で超過
→ Step 4 で TOC: QA ステップが制約（待ち時間60%）
→ Step 5 で SA Team × 3 + Platform Team を設計
→ Step 6 で DORA 改善計画: Lead Time 3週間→3日（6ヶ月目標）
→ Step 7 で Isolation パターンで段階的に SA チーム組成
→ 成果物: 依存分析レポート + チーム再編成計画 + DORA ロードマップ
```

### Example 2: マイクロサービス運用疲弊の解消

```
「チームが15個のマイクロサービスを担当して疲弊している」

→ Step 3 で認知負荷評価: 1チームが15 BC 所有（Commodity〜Custom-Built 混在）
  → Evolution Stage ヒューリスティクスで最大6 BC/teamが上限と判定
→ Step 2 で Expertise Dependencies: インフラ知識が2名に集中
→ Step 4 で TOC: デプロイパイプラインの手動ステップが制約
→ Step 5 で 3 SA Teams に分割 + Platform Team 組成
→ Step 5 で TVP 設計: 共通デプロイテンプレート + Observability 基盤
→ Step 7 で Grow and Split パターンで段階的分割
→ 成果物: 認知負荷マトリクス + チーム分割計画
```

### Example 3: レガシーシステムの段階的近代化

```
「モノリスの Big Ball of Mud を何とかしたい。チームは疲弊、技術的負債が山積み」

→ Step 1 で As-Is: BBoM、機能サイロ、テスト不足、月1デプロイ
→ Step 2 で Architecture Dependencies: 全変更が BE チーム経由（密結合）
→ Step 4 で VSM: Lead Time 4週間、VA 3日、Flow Efficiency 10%
→ Step 4 で TOC: BE チームが制約（全変更のゲートキーパー）
→ Step 5 で Platform Team（Isolation） → 効率ギャップ解消（Replatforming）
→ Step 5 で SA Team 段階組成（Generic BC から Quick Win）
→ Step 7 で Modular Monolith First → Strangler Fig で段階的抽出
→ 成果物: VSM + TOC 分析 + インクリメンタル移行ロードマップ
```

### Example 4: DORA メトリクス改善プロジェクト

```
「DORAメトリクスを計測して改善したい」

→ Step 1 で DORA ベースライン測定: Deploy Freq=月2回、Lead Time=10日、
  MTTR=2日、CFR=25%（Medium レベル）
→ Step 2 で Lead Time の内訳分析: レビュー待ち3日、QA待ち4日、デプロイ待ち2日
→ Step 4 で TOC: QA プロセスが制約（手動テスト比率が高い）
→ Step 6 で改善計画: 自動テスト拡充（CFR↓）、CI/CD 改善（Deploy Freq↑）、
  ペアプロ導入（Lead Time↓）
→ Step 6 で 3ヶ月目標: High レベル到達
→ 成果物: DORA 改善ロードマップ + アクションプラン
```

### Example 5: 新プロダクトチームの立ち上げ設計

```
「新規プロダクトの開発チームを立ち上げたい。最適な構成は?」

→ Step 1 で変更ストリーム特定: 3つの主要ユーザージャーニー
→ Step 3 で認知負荷見積: Core Domain（Genesis）= 1 BC/team
→ Step 5 で SA Team × 2 + Platform Team × 1 の初期構成
→ Step 5 で Collaboration モードで開始、知見が溜まったら XaaS に移行
→ Step 5 で TVP: ドキュメント + CI/CD テンプレートから開始
→ Step 7 で成長に応じた Grow and Split 計画
→ 成果物: チーム構成設計 + インタラクション進化計画
```

### Example 6: スプリント/イテレーション内のフロー改善

```
「スプリント内でタスクが完了しない。フローが悪い」

→ Step 1 で現状分析: WIP 過多、割り込み頻発、コンテキストスイッチ
→ Step 2 で Activity Dependencies: 3チーム間のレビュー待ち
→ Step 4 で VSM: スプリント内のプロセスステップをマッピング
→ Step 4 で TOC: コードレビュー待ちが制約（1名のシニアに集中）
→ Step 4 で Exploit: ペアプロ導入でレビュー待ちを排除
→ Step 4 で Subordinate: WIP 制限の導入
→ 成果物: スプリントフロー VSM + WIP 制限ガイドライン
```

---

## Troubleshooting

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| チームが現状の問題を言語化できない | 心理的安全性の不足、日常化した問題 | 「何に一番イライラするか」から始める。匿名サーベイも有効 |
| 依存関係が多すぎて分析が終わらない | スコープが広すぎる | 最も価値の高い1つの変更ストリームに絞って分析 |
| 認知負荷の定量化が難しい | 客観的指標がない | Evolution Stage ヒューリスティクスを初期近似として使用。チームの自己申告も参考に |
| TOC のボトルネックが特定できない | データ不足 | まずキューの蓄積を可視化。Kanban ボードの WIP 分布を確認 |
| DORA メトリクスを計測できない | ツール・プロセスが未整備 | 手動計測から開始。まず Deployment Frequency だけ追跡 |
| チーム再編成に抵抗がある | 変化への恐れ、帰属意識 | Dynamic Reteaming のセルフセレクションを活用。Calibration Session で安心感を醸成 |
| Platform Team の役割が不明確 | 責任範囲の曖昧さ | SA チームの「何に困っているか」から逆算。TVP で最小限から開始 |
| 改善が継続しない | 短期的な成果への圧力 | TOC の5ステップを反復。小さな改善を可視化して momentum を維持 |
| Big-bang 再編成を求められる | 経営層の期待・時間的制約 | インクリメンタル移行の早期成果を示す。リスクを定量的に提示 |
| SA チームが自律できない | スキル不足、依存関係が残存 | Enabling Team のコーチングを導入。Platform の XaaS 範囲を拡大 |

---

## References

| ファイル | 内容 |
|:---|:---|
| [cognitive-load-heuristics.md](references/cognitive-load-heuristics.md) | Evolution Stage → BC キャパシティ、Cynefin 補正、3 モダリティ評価テンプレート、Mindset Mix、Platform TVP 成熟度ラダー |
| [dora-benchmarks.md](references/dora-benchmarks.md) | DORA パフォーマンスレベル閾値、根本原因→DORA インパクトマトリクス、メトリクス別改善プレイブック、Westrum 文化モデル評価 |
| [vsm-template.md](references/vsm-template.md) | VSM 記法・テンプレート、ソフトウェアデリバリ典型ステップ、制約シグナル、TOC 5 ステップアクションテンプレート、Flow Efficiency ベンチマーク |
| [strands-py-runtime.md](references/strands-py-runtime.md) | strands-py（Strands Agent）上のツール・workspace・連携スキルの扱い |

## アンチパターン検出

このスキルの出力品質を検証するためのチェックリスト。

- [ ] DORA メトリクス改善の目標値が現状のベースラインからの具体的な数値で設定されているか
- [ ] VSM のボトルネック特定が TOC 5 ステップに基づいて実行されているか（直感での判断でないか）
- [ ] 認知負荷評価が 3 モダリティ（intrinsic/extraneous/germane）で分析されているか
- [ ] チーム再編成が Big-bang ではなくインクリメンタルに計画されているか
- [ ] Dynamic Reteaming の移行計画にステークホルダーの合意形成プロセスが含まれているか
- [ ] Flow Efficiency のベンチマーク値と現状値の比較が具体的な数値で提示されているか

---

## Related Skills

| スキル | 関係 | 説明 |
|:---|:---|:---|
| **flow-architecture** | Upstream（戦略） | Wardley Map + DDD + Team Topologies の戦略設計。project-ops はその戦略を運用レベルで実行する |
| **story-map** | Upstream | ユーザーニーズの構造化。変更ストリーム特定の入力として活用 |
| **diagram** | Downstream | 依存関係図、VSM、チーム構成図を draw.io で可視化 |
| **review** | Downstream | 依存分析・認知負荷評価・移行計画のクリティカルレビュー |
| **drm** | Downstream | チーム再編成の Go/No-Go 判断会議の準備・進行 |
| **data-validation** | Complementary | DORA メトリクスや VSM の数値整合性を検証 |
| **test** | Complementary | Change Failure Rate 改善のためのテスト戦略設計 |
| **incident-response** | Complementary | MTTR 改善のためのインシデント対応フロー・プレイブック。Step 6 DORA 改善の MTTR 施策を incident-response が具体化 |
| **observability** | Complementary | MTTR 改善のための SLO アラート・テレメトリ設計。Step 6 DORA 改善の検知速度向上を observability が提供 |
| **comm-craft** | Complementary | チーム再編成（Step 7）時のステークホルダー交渉・合意形成戦略。Dynamic Reteaming の合意形成に活用 |
