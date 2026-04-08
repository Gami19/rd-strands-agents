---
description: >
  アーキテクチャ設計の全ライフサイクルを管理するワークフロー。要件インテークから戦略的
  アーキテクチャ設計（Wardley Mapping・DDD・Team Topologies）、ソフトウェアアーキテクチャ
  選定（スタイル・特性・Quantum 分析）、詳細設計（C4・データ層・トレードオフ分析）、
  品質検証・ADR 記録、実装移行計画までを一貫してガイドする。
---

# Architecture Design ワークフロー

> 戦略・設計・意思決定の三位一体で、アーキテクチャを属人化させず組織知として鋳造する。

## ワークフロー全体像

```
Phase 0               Phase 1                 Phase 2                Phase 3               Phase 4
要件・制約の           アーキテクチャ          詳細アーキテクチャ     品質検証・             実装移行計画
インテーク             戦略策定                設計                   ADR 記録
  │                     │                       │                     │                     │
  ▼                     ▼                       ▼                     ▼                     ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 仕様取込      │──▶│ Wardley Map      │──▶│ C4 構成図生成    │──▶│ 設計レビュー     │──▶│ As-Built 図更新  │
│ 要件蒸留      │   │ DDD / BC 設計    │   │ データ層設計     │   │ ADR セルフ検証   │   │ 移行ロードマップ │
│ ストーリー分解│   │ スタイル選定     │   │ トレードオフ分析 │   │ リスク評価       │   │ Walking Skeleton │
│               │   │ Quantum 分析     │   │ ADR 生成         │   │ 数値検証         │   │ フィットネス関数 │
└──────────────┘   │ Team Topologies  │   └──────────────────┘  │ フィットネス関数 │  │ DRM             │
                    └──────────────────┘                         └──────────────────┘  └──────────────────┘
```

### 反復サイクル

Phase 2 と Phase 3 は反復して品質を高める。Phase 3 で問題が検出された場合、Phase 2 に戻り再設計を行う。

```
Phase 0 → Phase 1 → ┌─▶ Phase 2 ─▶ Phase 3 ─┐ → Phase 4
                     │                         │
                     └─── 品質未達時 ◀─────────┘
```

### 品質ゲート

| ゲート | 条件 | 不合格時のアクション |
|:---|:---|:---|
| Phase 0 → 1 | 全仕様が蒸留済み、ストーリーマップで設計スコープが確定 | Phase 0 に差し戻し |
| Phase 1 → 2 | 戦略アーキテクチャ方針が確定、Wardley Map/BC 設計/スタイル選定が完了 | Phase 1 に差し戻し |
| Phase 2 → 3 | 構成図 2 つ以上、ADR 記録済み、トレードオフ分析完了 | Phase 2 を継続 |
| Phase 3 → 4 | review で Critical/Major = 0、リスク高 (6-9) に緩和策あり | Phase 2 に差し戻し |
| Phase 4 | 移行ロードマップ完成、Walking Skeleton 定義済み、最終 ADR 記録済み | ― |

---

## Phase 0: 要件・制約のインテーク

### 概要

顧客資料・仕様書・技術ドキュメントを取り込み、アーキテクチャ設計の入力として構造化する。ストーリーマッピングで設計対象のスコープを可視化し、非機能要件を明確にする。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **pdf-convert** | 仕様書・RFP・技術資料の Markdown 変換 | 「仕様書を project/10_inbox に取り込んで」 |
| **distill** | 要件の蒸留・構造化（用語集、ドメインモデル、非機能要件） | 「project/10_inbox を project/20_notes に蒸留して」「用語集を作って」 |
| **story-map** | ユーザーストーリーマッピング、設計スコープ定義 | 「ストーリーマップを作成して」「MVP を定義して」 |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| 仕様書（Markdown 化済み） | `.md` | `project/10_inbox/` |
| 用語集 | `.md` | `project/20_notes/glossary.md` |
| ドメインモデル | `.md` | `project/20_notes/domain-model.md` |
| 非機能要件 | `.md` | `project/20_notes/non-functional-requirements.md` |
| ストーリーマップ | `.md` | `project/20_notes/story-map.md` |

### チェックリスト（Phase 0 → Phase 1 ゲート）

- [ ] 全仕様書が `project/10_inbox/` に Markdown 化されている
- [ ] 用語集でドメイン用語が統一されている
- [ ] ドメインモデルが作成されている（エンティティ・集約の概要）
- [ ] 非機能要件（性能、セキュリティ、可用性、スケーラビリティ等）が定義されている
- [ ] ストーリーマップでアーキテクチャ設計の対象スコープが明確になっている

### 次工程への引き渡し

```
「flow-architecture で Wardley Map と BC 設計をして」
「software-architecture でアーキテクチャ特性を分析してスタイルを選定して」
```

---

## Phase 1: アーキテクチャ戦略策定

### 概要

蒸留された要件に基づき、戦略レベルのアーキテクチャ設計を行う。flow-architecture でビジネス戦略（Wardley Mapping）、ドメイン設計（DDD/BC）、チーム組織（Team Topologies）の三位一体で社会技術システムを設計する。同時に software-architecture でアーキテクチャ特性の抽出、Quantum 分析、スタイル選定を行う。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **flow-architecture** | Wardley Map 作成、Subdomain 分類（Core/Supporting/Generic）、Bounded Context 設計、Team Topologies 適用、Architecture for Flow Canvas | 「フローアーキテクチャを設計して」「Wardley Map を作って」「BC を設計して」「チーム構成を最適化して」 |
| **software-architecture** | アーキテクチャ特性（-ilities）の抽出と優先順位付け、Quantum 分析、アーキテクチャスタイル選定（9 種比較）、コンポーネント設計 | 「アーキテクチャスタイルを選定して」「モノリスか分散か判断したい」「特性を分析して」 |
| **story-map** | BC 設計のアンカーとなるユーザーニーズの構造化 | 「ユーザーニーズを整理して」 |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| Wardley Map 記述 | `.md` | `docs/architecture/wardley-map.md` |
| Subdomain 分類（Core/Supporting/Generic） | `.md` | `docs/architecture/subdomain-classification.md` |
| Bounded Context 設計 + Context Map | `.md` | `docs/architecture/bounded-context.md` |
| Team Constellation（チーム編成計画） | `.md` | `docs/architecture/team-design.md` |
| Architecture for Flow Canvas | `.md` | `docs/architecture/flow-canvas.md` |
| アーキテクチャ特性分析 | `.md` | `docs/architecture/characteristics.md` |
| Quantum 分析 | `.md` | `docs/architecture/quantum-analysis.md` |
| スタイル選定レポート | `.md` | `docs/architecture/style-selection.md` |

### チェックリスト（Phase 1 → Phase 2 ゲート）

- [ ] Wardley Map でコンポーネントの Evolution Stage がマッピングされている
- [ ] Subdomain 分類で Core Domain が特定され、投資方針が決定されている
- [ ] Bounded Context が明確な境界と責任を持ち、Context Map パターンが定義されている
- [ ] アーキテクチャ特性が 7 個以内に絞り込まれ、優先順位が付いている
- [ ] Quantum 分析でモノリス/分散の判断が完了している
- [ ] アーキテクチャスタイルが選定され、根拠が明文化されている
- [ ] Team Topologies でチーム編成の方向性が定義されている

### Agent Teams による並行実行

Phase 1 では以下の並行実行が効果的:

```
「Agent Team で以下を並行実行して:
  - Teammate 1: flow-architecture で Wardley Map + Subdomain 分類 + BC 設計
  - Teammate 2: software-architecture でアーキテクチャ特性分析 + Quantum 分析」
```

### 次工程への引き渡し

```
「diagram で C4 コンテキスト図とコンテナ図を作成して」
「data-arch でデータアーキテクチャを設計して」
「decision-framework でスタイル選定の ADR を構造化して」
```

---

## Phase 2: 詳細アーキテクチャ設計

### 概要

Phase 1 の戦略方針に基づき、詳細レベルのアーキテクチャ設計を行う。diagram で構成図（C4 モデル、データフロー図、ネットワーク図）を作成し、data-arch でデータ層を設計する。decision-framework で全ての設計判断をトレードオフ分析付きの ADR として記録する。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **diagram** | C4 モデル図（コンテキスト/コンテナ/コンポーネント）、データフロー図、ネットワーク図、Context Map の可視化 | 「C4 コンテキスト図を描いて」「データフロー図を作って」「構成図を生成して」 |
| **data-arch** | データアーキテクチャ選定・設計（DWH/Data Lake/Lakehouse/Data Mesh）、データモデリング、ETL/ELT 設計 | 「データアーキテクチャを選定して」「データモデルを設計して」 |
| **decision-framework** | トレードオフ分析（重み付きマトリクス）、ADR 生成（7 セクション構造）、DACI/RACI チャート、リスクストーミング | 「トレードオフを分析して」「ADR を書いて」「DACI を作って」 |
| **software-architecture** | コンポーネント設計の詳細化、結合度評価 | 「コンポーネント間の結合度を評価して」 |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| C4 コンテキスト図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| C4 コンテナ図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| データフロー図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| ネットワーク構成図（該当時） | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| データアーキテクチャ設計書 | `.md` | `docs/architecture/` |
| トレードオフ分析マトリクス | `.md` | `docs/architecture/` |
| ADR（設計判断記録） | `.md` | `project/50_decision_log/` |
| DACI / RACI チャート | `.md` | `docs/architecture/` |

### ADR 記録

設計判断が発生した時点で `project/50_decision_log/` に ADR 形式で記録する。decision-framework の 7 セクション構造を使用。

```
# ADR naming convention
project/50_decision_log/ADR-NNNN-<summary>.md

# Examples
project/50_decision_log/ADR-0001-architecture-style-service-based.md
project/50_decision_log/ADR-0002-data-architecture-lakehouse.md
project/50_decision_log/ADR-0003-communication-protocol-grpc.md
project/50_decision_log/ADR-0004-tenant-isolation-schema-per-tenant.md
```

### チェックリスト（Phase 2 → Phase 3 ゲート）

- [ ] 構成図が最低 2 つ作成されている（C4 コンテキスト + コンテナ、またはデータフロー図）
- [ ] データアーキテクチャが設計されている（該当する場合）
- [ ] 全ての重要な設計判断に ADR が記録されている
- [ ] トレードオフ分析で選定根拠が定量的に示されている
- [ ] DACI / RACI でステークホルダーの役割が整理されている
- [ ] コンポーネント間のインターフェースが定義されている

### Agent Teams による並行実行

```
「Agent Team で以下を並行実行して:
  - Teammate 1: diagram で C4 コンテキスト図 + コンテナ図を作成
  - Teammate 2: data-arch でデータアーキテクチャを設計
  - Teammate 3: decision-framework でスタイル選定の ADR + トレードオフ分析」
```

### 次工程への引き渡し

```
「review でアーキテクチャ設計書をレビューして」
「decision-framework でリスク評価を実施して」
「data-validation で見積数値の整合性を検証して」
```

---

## Phase 3: 品質検証・ADR 記録

### 概要

設計成果物を多角的に検証する。review でアーキテクチャ設計書・構成図・ADR の品質をクリティカルレビューし、decision-framework でリスク評価とフィットネス関数の設計を行う。data-validation で見積数値やスコアリングの整合性を検証する。品質未達の場合は Phase 2 に差し戻す。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **review** | 設計ドキュメントレビュー（要件カバレッジ、章間整合性、技術的正確性）、ADR レビュー | 「設計書をレビューして」「ADR の品質を検証して」 |
| **decision-framework** | リスクストーミング、リスクマトリクス構築、フィットネス関数設計、ADR ライフサイクル管理、アンチパターン検出 | 「リスク評価をして」「フィットネス関数を設計して」「判断のアンチパターンをチェックして」 |
| **data-validation** | トレードオフ分析のスコアリング整合性、見積数値の妥当性検証 | 「数値の整合性を検証して」「スコアリングを検証して」 |

### 品質検証フロー

```
詳細設計完了（Phase 2）
  │
  ├─▶ review（設計ドキュメント + ADR レビュー）
  │     ├─ Critical/Major = 0 ──▶ 次へ
  │     └─ Critical/Major あり ──▶ Phase 2 に差し戻し
  │
  ├─▶ decision-framework（リスク評価）
  │     ├─ 高リスク (6-9) に緩和策あり ──▶ 次へ
  │     └─ 緩和策不足 ──▶ Phase 2 に差し戻し
  │
  ├─▶ data-validation（数値検証）
  │     ├─ 整合 ──▶ 次へ
  │     └─ 不整合 ──▶ Phase 2 に差し戻し
  │
  └─▶ decision-framework（フィットネス関数設計）
        └─ 高影響 ADR にフィットネス関数を設計
```

### レビュー観点

**設計ドキュメントレビュー（review スキル）**:
- A-1: 要件カバレッジ -- 非機能要件への対応漏れがないか
- A-2: 章間整合性 -- Wardley Map / BC 設計 / スタイル選定 / 構成図の一貫性
- A-3: 技術的正確性 -- アーキテクチャパターンの正しい適用
- A-4: 可読性 -- ステークホルダーに説明可能な形式か

**ADR レビュー（review + decision-framework）**:
- Decision セクションの Why が十分に記述されているか
- Consequences にポジティブ・ネガティブ両面が記載されているか
- Alternatives に検討した代替案が含まれているか
- 意思決定アンチパターン（Covering Your Assets / Groundhog Day / HiPPO）が検出されないか

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| 設計レビューレポート | `.md` | `docs/reviews/` |
| リスク評価レポート（リスクマトリクス + 緩和策） | `.md` | `docs/architecture/` |
| フィットネス関数設計書 | `.md` | `docs/architecture/` |
| 数値検証レポート | `.md` | `docs/reviews/` |

### 完了条件（品質ゲート）

| ゲート | 条件 | 不合格時 |
|:---|:---|:---|
| 設計レビュー | Critical / Major の指摘が 0 件 | Phase 2 に差し戻し |
| リスク評価 | 高リスク (6-9) 全てに緩和策策定済み | Phase 2 に差し戻し |
| 数値検証 | トレードオフスコアリング・見積数値が整合 | Phase 2 に差し戻し |
| ADR 品質 | 全 ADR に Why が記述、アンチパターン非検出 | ADR を修正 |

### Agent Teams による並行実行

```
「Agent Team で以下を並行実行して:
  - Teammate 1: review で設計ドキュメントをレビュー
  - Teammate 2: decision-framework でリスク評価 + フィットネス関数設計
  - Teammate 3: data-validation でスコアリングと数値の整合性を検証」
```

### 次工程への引き渡し

```
# Quality gate passed
「diagram で構成図を最終版に更新して」
「flow-architecture の移行ロードマップに基づいて実装計画を策定して」
```

---

## Phase 4: 実装移行計画

### 概要

品質検証を通過した設計成果物に基づき、実装への移行計画を策定する。構成図の As-Built 更新、Walking Skeleton の定義、移行ロードマップの策定、フィットネス関数の CI/CD 組み込み計画を行う。DRM でアーキテクチャ承認会議を実施する。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **diagram** | As-Built 構成図の最終更新、移行フェーズ図 | 「構成図を最新化して」「移行フェーズ図を作って」 |
| **flow-architecture** | Transition Roadmap（Strangler Fig / インクリメンタル移行） | 「移行ロードマップを策定して」「段階的移行計画を作って」 |
| **decision-framework** | 最終 ADR（移行戦略、リリース判断）、ADR 棚卸し | 「移行戦略の ADR を書いて」「ADR を棚卸しして」 |
| **drm** | アーキテクチャ承認会議（Go/No-Go 判定）の台本生成 | 「アーキテクチャ承認会議を準備して」「DRM アジェンダを作って」 |
| **review** | 最終レビュー（移行計画の妥当性） | 「移行計画をレビューして」 |
| **agent-craft** | プロジェクト固有のアーキテクチャ監視エージェント作成（任意） | 「アーキテクチャ監視エージェントを作って」 |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| 最終構成図（As-Built） | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| 移行ロードマップ | `.md` | `docs/architecture/` |
| Walking Skeleton 定義 | `.md` | `docs/architecture/` |
| フィットネス関数 CI/CD 組み込み計画 | `.md` | `docs/architecture/` |
| DRM 台本（アーキテクチャ承認） | `.md` | `project/60_snapshots/` |
| 最終 ADR（移行戦略、承認判断） | `.md` | `project/50_decision_log/` |
| カスタムエージェント（任意） | `.md` | `.claude/agents/` |

### 移行計画の策定

flow-architecture の Transition Roadmap に基づき、インクリメンタルな移行計画を策定する。

```
Phase A: Foundation（基盤整備）
  - Walking Skeleton の実装
  - Platform Team の組成（該当時）
  - フィットネス関数の CI/CD 組み込み

Phase B: First Stream（最初の価値提供）
  - Core Domain の最初の BC を実装
  - ACL でレガシーとの境界を設定（移行案件の場合）
  - 初期メトリクス収集開始

Phase C: Expand（拡張）
  - 次の BC を段階的に実装・抽出
  - Platform の XaaS 化（該当時）
  - アーキテクチャの継続的検証

Phase D: Optimize（最適化）
  - フロー指標の継続的改善
  - チームインタラクションの進化
  - ADR の定期棚卸し
```

### チェックリスト（Phase 4 完了条件）

- [ ] 構成図が最終版（As-Built）に更新されている
- [ ] 移行ロードマップがフェーズ分けで策定されている
- [ ] Walking Skeleton が定義され、最初に実装すべき範囲が明確
- [ ] フィットネス関数の CI/CD 組み込み計画がある
- [ ] DRM でアーキテクチャ承認の Go 判定を取得した（または Go 条件を明確化）
- [ ] ADR が全フェーズにわたって記録されている
- [ ] 設計書と構成図が整合している

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| Phase 0 で非機能要件が曖昧 | ステークホルダーから明確な要件が出ない | distill でビジネスコンテキストから暗黙的な特性を推定。具体的な質問リストで引き出す |
| Phase 1 で Wardley Map を作り始められない | スコープが広すぎる、ユーザーが不明確 | 1人のユーザーと1つのニーズから始める。完璧さより有用性を目指す |
| Phase 1 で Core Domain が特定できない | 差別化要因の理解不足 | 「これがなくなったら競争優位を失うか?」を各領域に問う |
| Phase 1 でスタイル選定が決まらない | 特性が絞れていない、Quantum 分析が不十分 | software-architecture の Step 2-3 を再実施。特性を 7 個以内に絞る |
| Phase 1 で flow-architecture と software-architecture の結果が矛盾 | 分析の粒度・視点の差異 | flow-architecture の BC 設計と software-architecture の Quantum 分析を突合する |
| Phase 2 で構成図が不完全 | コンポーネント間のインターフェース未定義 | project/20_notes の API 仕様を先に策定。BC の Context Map パターンを参照 |
| Phase 2 で ADR が長すぎる | 分析を詰め込みすぎ | ADR は 1-2 ページ。詳細はトレードオフ分析を別ファイルに分離 |
| Phase 3 で review の Critical が大量 | Phase 1 の戦略と Phase 2 の詳細が乖離 | Phase 1 の戦略文書に立ち返り、一貫性を再確認 |
| Phase 3 で同じ決定が蒸し返される | ADR が共有・発見されていない | decision-framework の Groundhog Day 矯正策を適用。ADR をリポジトリに集約 |
| Phase 3 → Phase 2 の差し戻しが繰り返される | 品質基準が高すぎるか要件が不安定 | Phase 0 に戻り要件を再確認。品質基準自体を ADR で明文化 |
| Phase 4 で移行計画が Big-bang になる | 経営層の期待、時間的制約 | リスクを定量的に提示。Strangler Fig パターンの早期成果を示す |
| Phase 4 で構成図と設計が乖離 | Phase 2-3 の変更が未反映 | diagram に差分更新を依頼。ADR から変更を追跡 |

---

## スキル発動マトリクス（全フェーズ × 全スキル）

| スキル | Ph.0 | Ph.1 | Ph.2 | Ph.3 | Ph.4 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **pdf-convert** | **主** | - | - | - | - |
| **distill** | **主** | - | - | - | - |
| **story-map** | **主** | **補** | - | - | - |
| **flow-architecture** | - | **主** | - | - | **主** |
| **software-architecture** | - | **主** | **補** | - | - |
| **diagram** | - | - | **主** | - | **主** |
| **data-arch** | - | - | **主** | - | - |
| **decision-framework** | - | - | **主** | **主** | **主** |
| **review** | - | - | - | **主** | **補** |
| **data-validation** | - | - | - | **主** | - |
| **drm** | - | - | - | - | **主** |
| **agent-craft** | - | - | - | - | **補** |

**凡例**: **主** = フェーズの主要スキル、**補** = 補助的に使用、- = 不使用

---

## スキル間連携図

```
Phase 0: 要件・制約のインテーク
┌────────────────────────────────┐
│ pdf-convert → distill          │
│                → story-map     │
└──────────────┬─────────────────┘
               │
               ▼
Phase 1: アーキテクチャ戦略策定
┌────────────────────────────────┐
│ flow-architecture              │
│   ├─ Wardley Map               │
│   ├─ DDD / BC / Context Map    │
│   └─ Team Topologies           │
│                                │
│ software-architecture          │
│   ├─ 特性 (-ilities) 抽出      │
│   ├─ Quantum 分析              │
│   └─ スタイル選定              │
│                                │
│ story-map ─▶ ユーザーニーズ     │
└──────────────┬─────────────────┘
               │
               ▼
Phase 2: 詳細アーキテクチャ設計
┌────────────────────────────────┐
│ diagram ◀── BC + コンポーネント │
│   ├─ C4 コンテキスト/コンテナ  │
│   ├─ データフロー図            │
│   └─ ネットワーク構成図        │
│                                │
│ data-arch ◀── 要件 + スタイル  │
│   └─ データ層設計              │
│                                │
│ decision-framework             │
│   ├─ トレードオフ分析          │
│   ├─ ADR 生成                  │
│   └─ DACI / RACI              │
│                                │
│ software-architecture（補助）  │
│   └─ コンポーネント設計詳細化  │
└──────────────┬─────────────────┘
               │     ▲
               │     │ 品質未達時
               ▼     │
Phase 3: 品質検証・ADR 記録 ★
┌────────────────────────────────┐
│ review（設計 + ADR レビュー）  │
│ decision-framework             │
│   ├─ リスク評価                │
│   ├─ フィットネス関数設計      │
│   └─ アンチパターン検出        │
│ data-validation（数値検証）    │
└──────────────┬─────────────────┘
               │
               ▼
Phase 4: 実装移行計画
┌────────────────────────────────┐
│ diagram（As-Built 最終版）     │
│ flow-architecture              │
│   └─ Transition Roadmap        │
│ decision-framework             │
│   ├─ 最終 ADR                  │
│   └─ ADR 棚卸し               │
│ drm（アーキテクチャ承認会議）  │
│ review（移行計画レビュー）     │
│ agent-craft（監視エージェント） │
└────────────────────────────────┘
```

---

## ディレクトリ構造テンプレート

```
<project-root>/
├── project/
│   ├── 10_inbox/               ← Phase 0: 仕様書・技術資料（Markdown 化済み）
│   ├── 20_notes/               ← Phase 0: 蒸留済み要件
│   │   ├── glossary.md
│   │   ├── domain-model.md
│   │   ├── non-functional-requirements.md
│   │   └── story-map.md
│   ├── 50_decision_log/        ← Phase 2-4: ADR（設計判断記録）
│   │   ├── ADR-0001-*.md
│   │   └── ...
│   ├── 60_snapshots/           ← Phase 4: DRM 台本
│   ├── 90_references/          ← 外部参照資料
│   └── 00_schemas/             ← ドキュメントスキーマ定義
├── docs/                  ← Phase 1-4: 設計ドキュメント
│   ├── architecture/         アーキテクチャ設計書群
│   │   ├── wardley-map.md
│   │   ├── subdomain-classification.md
│   │   ├── bounded-context.md
│   │   ├── team-design.md
│   │   ├── flow-canvas.md
│   │   ├── characteristics.md
│   │   ├── quantum-analysis.md
│   │   ├── style-selection.md
│   │   ├── data-architecture.md
│   │   ├── tradeoff-analysis.md
│   │   ├── risk-assessment.md
│   │   ├── fitness-functions.md
│   │   ├── migration-roadmap.md
│   │   └── walking-skeleton.md
│   ├── diagrams/             構成図（.drawio / .drawio.svg）
│   │   ├── c4-context.drawio
│   │   ├── c4-container.drawio
│   │   ├── data-flow.drawio
│   │   └── migration-phases.drawio
│   └── reviews/              レビューレポート
├── .agents/
│   ├── skills/               導入済みスキル群
│   └── workflows/            ワークフロー定義
└── CLAUDE.md              ← プロジェクト設定
```

---

## クイックスタート: 典型的なアーキテクチャ設計の進め方

### パターン A: 新規システムのフルアーキテクチャ設計

```
1. 「この仕様書を project/10_inbox に取り込んで」                     → pdf-convert
2. 「project/10_inbox を project/20_notes に蒸留して」                 → distill
3. 「ストーリーマップでスコープを定義して」                         → story-map
4. 「Wardley Map を作って BC を設計して」                          → flow-architecture
5. 「アーキテクチャ特性を分析してスタイルを選定して」               → software-architecture
6. 「C4 コンテキスト図とコンテナ図を描いて」                       → diagram
7. 「データアーキテクチャを設計して」                               → data-arch
8. 「スタイル選定の ADR をトレードオフ分析付きで書いて」           → decision-framework
9. 「設計書をレビューして」                                         → review
10. 「リスク評価をして」                                           → decision-framework
11. 「移行ロードマップを策定して」                                 → flow-architecture
12. 「アーキテクチャ承認会議を準備して」                           → drm
```

### パターン B: レガシーシステムの近代化

```
1. 「現行システムの情報を project/10_inbox に取り込んで蒸留して」     → pdf-convert + distill
2. 「フローアーキテクチャで As-Is を評価して」                     → flow-architecture
3. 「アーキテクチャ特性を分析して移行先のスタイルを選定して」       → software-architecture
4. 「As-Is/To-Be の構成図を描いて」                               → diagram
5. 「Strangler Fig パターンで段階的移行計画を策定して」            → flow-architecture
6. 「移行戦略の ADR を書いて」                                     → decision-framework
7. 「設計をレビューして」                                           → review
```

### パターン C: 技術選定のアーキテクチャ判断

```
1. 「アーキテクチャ特性を分析して」                                 → software-architecture
2. 「候補のトレードオフを分析して」                                 → decision-framework
3. 「リスク評価をして」                                             → decision-framework
4. 「ADR を書いて」                                                 → decision-framework
5. 「ADR をレビューして」                                           → review
```

### パターン D: 組織とアーキテクチャの整合

```
1. 「チームとアーキテクチャを最適化したい」                         → flow-architecture
2. 「チーム認知負荷を検証して」                                     → flow-architecture
3. 「Team Topologies でチーム編成を設計して」                       → flow-architecture
4. 「構成図を描いて」                                               → diagram
5. 「再編成計画をレビューして」                                     → review
```

---

## 関連ワークフロー

| ワークフロー | 関係 |
|:---|:---|
| [engineering-workflow.md](engineering-workflow.md) | 実装フェーズの詳細ライフサイクル（Phase 4 以降の開発に接続） |
| [bd-skills-workflow.md](bd-skills-workflow.md) | BD ワークフロー（BD 案件の技術設計として Phase 1-2 を併用） |
| [proposal-lifecycle.md](proposal-lifecycle.md) | 提案書作成（アーキテクチャ設計結果を提案書に組み込む場合に併用） |
| [convert-pdf.md](convert-pdf.md) | PDF 変換の詳細手順（Phase 0 の深掘り） |
