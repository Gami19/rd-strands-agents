---
description: >
  SRE/DevOps の運用設計から、オブザーバビリティ基盤構築、監視・アラート体制、インシデント対応
  プロセス、ポストモーテム・継続改善までを一気通貫で支援するワークフロー。
  incident-response / observability を中核に、diagram / review / data-validation を
  フェーズごとにオーケストレーションする。将来的に cicd-design スキルを統合予定。
---

# 運用設計ワークフロー（Operations）

> SLO 設計からオブザーバビリティ基盤、インシデント対応体制、ポストモーテム文化まで、本番運用の信頼性を一気通貫で構築する。

## ワークフロー全体像

```
Phase 0               Phase 1                 Phase 2                Phase 3               Phase 4
運用要件               オブザーバビリティ      監視・アラート         インシデント対応       ポストモーテム・
インテーク             基盤設計                体制構築               プロセス構築           継続改善
  |                     |                       |                     |                     |
  v                     v                       v                     v                     v
+--------------+   +------------------+   +------------------+  +------------------+  +------------------+
| SLO 目標設定  |-->| 構造化イベント    |-->| SLO ベースアラート|-->| ICS 体制設計     |-->| 非難なしレビュー |
| SLI 定義      |   |  設計            |   | Four Golden      |   | エスカレーション |   | アクション追跡   |
| 運用要件蒸留  |   | 分散トレーシング |   |  Signals         |   | プレイブック     |   | 運用改善サイクル |
| 成熟度評価    |   | OTel 計装戦略    |   | オンコール設計   |   | 障害対策         |   | 訓練計画         |
|               |   | パイプライン設計 |   | ダッシュボード   |   | 訓練設計         |   |                  |
+--------------+   +------------------+   +------------------+  +------------------+  +------------------+
```

### 反復サイクル

Phase 3 と Phase 4 は反復して運用の成熟度を高める。ポストモーテムで発見された改善点がインシデント対応プロセスの更新にフィードバックされる。また Phase 2 と Phase 3 の間でも、監視体制の不備がインシデント対応で露呈した場合に差し戻しが発生する。

```
Phase 0 --> Phase 1 --> Phase 2 --> +-> Phase 3 --> Phase 4 -+
                          ^         |                         |
                          |         +--- 改善フィードバック <-+
                          |
                          +--- 監視不備の検出時に差し戻し
```

### 品質ゲート（Phase 間の通過条件）

| ゲート | 条件 | 不合格時のアクション |
|:---|:---|:---|
| Phase 0 -> 1 | SLI/SLO が定義済み、エラーバジェットポリシー策定済み、OMM 評価完了 | Phase 0 に差し戻し |
| Phase 1 -> 2 | 構造化イベント設計完了、OTel 計装戦略確定、パイプライン設計完了 | Phase 1 に差し戻し |
| Phase 2 -> 3 | SLO ベースアラート設計完了、オンコール体制設計済み、ダッシュボード設計済み | Phase 2 に差し戻し |
| Phase 3 -> 4 | ICS 役割分担定義済み、プレイブック 3 パターン以上作成、訓練計画策定済み | Phase 3 に差し戻し |
| Phase 4（完了） | review で Critical/Major = 0、全数値検証済み、改善サイクル定義済み | 指摘修正後に再レビュー |

### ADR 記録タイミング

| Phase | ADR 記録タイミング | 記録内容の例 |
|:---|:---|:---|
| Phase 0 | SLO 目標値の決定時 | SLO 設定根拠、内部/外部 SLO の差分設計 |
| Phase 1 | 計装・パイプライン方針決定時 | OTel vs 独自計装の選定、バックエンドツール選定 |
| Phase 2 | アラート・オンコール方針決定時 | アラート閾値の根拠、ローテーション設計の判断 |
| Phase 3 | 対応フロー策定時 | ICS 採用の根拠、エスカレーションレベルの設計判断 |
| Phase 4 | 改善施策決定時 | ポストモーテムから導出された改善の優先順位判断 |

ファイル命名規則: `project/50_decision_log/ADR-NNNN-<判断概要>.md`

---

## Phase 0: 運用要件インテーク

### 概要

対象サービスの運用要件を整理し、信頼性目標（SLO/SLI）を定量的に設計する。オブザーバビリティ成熟度（OMM）の現状評価を行い、改善ロードマップの基盤を構築する。既存の運用ドキュメントがある場合は蒸留してからインプットとする。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **incident-response** | SLI 選定、SLO 設計、エラーバジェットポリシー策定 | 「SLO を設計して」「エラーバジェットを設計して」「SLI を定義して」 |
| **observability** | OMM 5 能力の成熟度評価、優先能力の特定 | 「オブザーバビリティ成熟度を評価して」「現状を診断して」 |
| **distill**（補助） | 既存運用ドキュメント・障害報告書の蒸留 | 「運用ドキュメントを蒸留して」「過去の障害報告を整理して」 |
| **pdf-convert**（補助） | 運用マニュアル PDF の Markdown 変換 | 「運用マニュアルを変換して」 |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| SLI/SLO 定義書 | `.md` | `docs/operations/slo-definition.md` |
| エラーバジェットポリシー | `.md` | `docs/operations/error-budget-policy.md` |
| OMM 成熟度評価レポート | `.md` | `docs/operations/omm-assessment.md` |
| 運用要件サマリー | `.md` | `project/20_notes/operational-requirements.md` |
| 改善ロードマップ | `.md` | `docs/operations/improvement-roadmap.md` |

### チェックリスト（Phase 0 -> Phase 1 ゲート）

- [ ] ユーザー視点の SLI を 2-4 個選定した（パーセンタイルベース、平均値不使用）
- [ ] SLO 目標値をビジネス要件から導出した（現行実績からの逆算ではない）
- [ ] エラーバジェットを算出し、枯渇時のアクションポリシーを文書化した
- [ ] OMM 5 能力（障害回復力、コード品質、技術的負債、リリースケイデンス、ユーザー理解）を評価した
- [ ] 優先改善能力を特定し、ステークホルダーの合意を得た
- [ ] 既存の監視状況・運用課題を棚卸しした

### 次工程への引き渡し

```
「observability スキルで構造化イベントを設計して」
「observability スキルで OTel 計装戦略を策定して」
```

---

## Phase 1: オブザーバビリティ基盤設計

### 概要

Phase 0 で定義した SLO を計測するためのオブザーバビリティ基盤を設計する。構造化イベント設計、分散トレーシング、OpenTelemetry 計装戦略、テレメトリパイプライン、サンプリング戦略を一括して策定する。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **observability** | 構造化イベント設計、分散トレーシング設計、OTel 計装戦略、サンプリング戦略、テレメトリパイプライン設計 | 「構造化イベントを設計して」「OTel 計装を設計して」「テレメトリパイプラインを構築したい」 |
| **diagram** | テレメトリパイプラインアーキテクチャ図、トレースフロー図、データフロー図 | 「パイプライン構成図を描いて」「トレーシング構成を図にして」 |
| **data-validation**（補助） | サンプリング率・コスト見積の数値検証 | 「サンプリング率を検証して」「テレメトリコスト見積を確認して」 |

### 設計スコープ

```
1. 構造化イベント設計
   ├── イベントスコープ定義（1 イベント = 1 リクエスト/1 サービス）
   ├── 必須フィールド（trace_id, span_id, timestamp, duration_ms 等）
   ├── 高カーディナリティフィールド（user_id, request_id, build_id 等）
   └── ビジネスコンテキストフィールド

2. 分散トレーシング設計
   ├── スパン親子関係の設計
   ├── トレースコンテキスト伝搬標準の選択（W3C TraceContext 推奨）
   └── カスタムスパンの優先順位（クリティカルパス優先）

3. OpenTelemetry 計装戦略
   ├── 自動計装の対象フレームワーク特定
   ├── カスタム計装の優先順位
   └── エクスポート先の決定（Collector / 直接）

4. サンプリング戦略
   ├── トラフィック量に応じた戦略選択
   ├── Head/Tail サンプリングの方針
   └── サンプルレートのイベント内記録設計

5. テレメトリパイプライン設計
   ├── OTel Collector 構成（Agent + Gateway）
   ├── バッファリング戦略（Kafka 等）
   ├── PII マスキング・コンプライアンス
   └── パイプライン自体のモニタリング
```

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| 構造化イベント設計書（フィールド定義） | `.md` | `docs/operations/event-design.md` |
| 分散トレーシング設計書 | `.md` | `docs/operations/tracing-design.md` |
| OTel 計装ガイド | `.md` + コード例 | `docs/operations/otel-instrumentation.md` |
| サンプリング戦略設計書 | `.md` | `docs/operations/sampling-strategy.md` |
| テレメトリパイプライン設計書 | `.md` | `docs/operations/telemetry-pipeline.md` |
| パイプラインアーキテクチャ図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| ADR（計装・ツール選定判断） | `.md` | `project/50_decision_log/` |

### チェックリスト（Phase 1 -> Phase 2 ゲート）

- [ ] 高カーディナリティフィールドを 10 個以上設計した
- [ ] サービス間のスパン親子関係を図示した
- [ ] トレースコンテキスト伝搬の標準を選択した（W3C / B3）
- [ ] OTel 自動計装の対象フレームワークを特定した
- [ ] サンプリング戦略を選択し、エラーイベントの確実な捕捉を設計した
- [ ] テレメトリパイプラインのアーキテクチャ図を作成した
- [ ] PII マスキング・コンプライアンス要件を反映した

### Agent Teams による並行実行

Phase 1 では以下の並行実行が効果的:

```
「Agent Team で以下を並行実行して:
  - Teammate 1: observability で構造化イベント + トレーシング + 計装設計
  - Teammate 2: diagram でテレメトリパイプラインアーキテクチャ図を作成」
```

### 次工程への引き渡し

```
「incident-response スキルで SLO ベースアラートを設計して」
「incident-response スキルでオンコール体制を設計して」
```

---

## Phase 2: 監視・アラート体制構築

### 概要

Phase 1 で設計したオブザーバビリティ基盤の上に、SLO ベースアラート、Four Golden Signals 監視、オンコール体制を構築する。従来の閾値ベースアラートから SLO ベースアラートへの移行戦略も設計する。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **observability** | SLO ベースアラート設計（予測バーンアラート）、既存アラートの整理 | 「SLO ベースアラートを設計して」「アラート疲れを解消したい」 |
| **incident-response** | Four Golden Signals 監視設計、オンコール体制設計、エスカレーションパス | 「監視を設計して」「オンコール体制を整備して」 |
| **diagram** | 監視アーキテクチャ図、エスカレーションフロー図、ダッシュボード設計図 | 「監視構成図を描いて」「エスカレーションフローを図にして」 |
| **data-validation**（補助） | アラート閾値・エラーバジェット消費率の数値検証 | 「アラート閾値を検証して」「エラーバジェット消費率を確認して」 |
| **review**（補助） | 監視・アラート設計のレビュー | 「監視設計をレビューして」 |

### アラート設計の原則

すべてのページングアラートが以下を満たすことを検証する:

1. **緊急** -- 即時対応が必要
2. **アクション可能** -- 対応者が具体的なアクションを取れる
3. **ユーザー影響あり** -- ユーザーに実際の影響が出ている（または差し迫っている）
4. **新規** -- ロボット的対応で済むなら自動化すべき

### SLO ベースアラートへの移行パス

```
Step 1: SLI をイベントベースで定義（クリティカルユーザージャーニーごと）
  |
  v
Step 2: 予測バーンアラートを設計
  ├── 短期: 1h ベースライン --> 4h 予測（ページング）
  └── 長期: 6h ベースライン --> 24h 予測（通知）
  |
  v
Step 3: 既存閾値アラートと並行運用（信頼性実証期間）
  |
  v
Step 4: SLO アラートの実績を蓄積し、段階的に閾値アラートを廃止
```

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| Four Golden Signals 監視設計書 | `.md` | `docs/operations/monitoring-design.md` |
| SLO ベースアラート設計書 | `.md` | `docs/operations/slo-alerting.md` |
| オンコール体制設計書（ローテーション、エスカレーション） | `.md` | `docs/operations/on-call-design.md` |
| ダッシュボード設計書 | `.md` | `docs/operations/dashboard-design.md` |
| 監視アーキテクチャ図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| エスカレーションフロー図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| ADR（アラート方針、オンコール設計判断） | `.md` | `project/50_decision_log/` |

### チェックリスト（Phase 2 -> Phase 3 ゲート）

- [ ] Four Golden Signals（Latency, Traffic, Errors, Saturation）にメトリクスを定義した
- [ ] 各アラートが「緊急・アクション可能・ユーザー影響あり」を満たす
- [ ] SLO ベースの予測バーンアラート（短期・長期）を設計した
- [ ] オンコール時間が全体の 25% 以下に収まるローテーションを設計した
- [ ] Primary / Secondary の役割分担とエスカレーションパスを定義した
- [ ] ダッシュボードに Four Golden Signals + SLO バーンダウンを表示する設計がある
- [ ] 既存アラートの棚卸しと移行計画を策定した

### Agent Teams による並行実行

```
「Agent Team で以下を並行実行して:
  - Teammate 1: observability で SLO ベースアラート設計
  - Teammate 2: incident-response で Four Golden Signals 監視 + オンコール体制設計
  - Teammate 3: diagram で監視構成図 + エスカレーションフロー図を作成」
```

### 次工程への引き渡し

```
「incident-response スキルでインシデント対応フローを設計して」
「incident-response スキルでプレイブックを作成して」
```

---

## Phase 3: インシデント対応プロセス構築

### 概要

ICS (Incident Command System) に基づくインシデント管理体制を構築する。インシデント宣言基準、役割分担、対応フロー、プレイブック、カスケード障害対策、訓練計画を設計する。Phase 2 で構築した監視・アラートが「検知」の仕組みなら、Phase 3 は「対応」の仕組みを担う。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **incident-response** | ICS 役割分担、インシデント対応フロー、プレイブック生成、カスケード障害対策、緊急対応パターン設計 | 「インシデント対応フローを設計して」「プレイブックを作成して」「カスケード障害対策を設計して」 |
| **diagram** | インシデント対応フロー図、エスカレーション図、カスケード障害対策フロー図 | 「インシデント対応フローを図にして」 |
| **review**（補助） | プレイブック・対応フローの品質レビュー | 「プレイブックをレビューして」 |

### インシデント対応フロー

```
障害検知（Phase 2 のアラート）
  |
  v
トリアージ（5 分以内）
  ├── 影響範囲の確認
  ├── 重大度の判定
  └── インシデント宣言の要否判断
  |
  v
インシデント宣言（基準: 2 チーム関与 / 顧客可視 / 1h 未解決）
  |
  v
ICS 発動
  ├── IC: 全体統括、役割割当
  ├── Ops Lead: システム操作
  ├── Comms Lead: ステータス更新（4h ごと）
  └── Planning Lead: バグ起票、ハンドオフ
  |
  v
止血・緩和（30 分以内を目標）
  ├── ロールバック / トラフィック迂回 / 負荷制限
  └── ライブドキュメントをリアルタイム更新
  |
  v
解決確認
  ├── Exit Criteria: SLO 内で 30 分安定 + 暫定修正適用済み
  └── ポストモーテムスケジュール設定 --> Phase 4 へ
```

### プレイブック設計

3 つの障害誘因パターンに対応するプレイブックを作成する:

| パターン | 典型的シナリオ | 対策の重点 |
|:---|:---|:---|
| テスト誘発型 | DR テスト、カオスエンジニアリングの予想外の影響 | テスト即時中止、影響範囲特定、ロールバック手順 |
| 変更誘発型 | 設定変更・デプロイによる障害 | カナリアリリース、ロールバック手順、変更管理 |
| プロセス誘発型 | 自動化バグによる大規模意図しない操作 | 全自動化停止、トラフィック迂回、サニティチェック |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| インシデント対応ガイド（ICS 役割、宣言基準、7 原則） | `.md` | `docs/operations/incident-response-guide.md` |
| インシデント状態ドキュメントテンプレート | `.md` | `docs/operations/templates/incident-status.md` |
| プレイブック（3 パターン以上） | `.md` | `docs/operations/playbooks/` |
| カスケード障害対策設計書 | `.md` | `docs/operations/cascade-failure-mitigation.md` |
| 訓練計画（Wheel of Misfortune, DiRT, ゲームデー） | `.md` | `docs/operations/training-plan.md` |
| インシデント対応フロー図 | `.drawio` / `.drawio.svg` | `docs/diagrams/` |
| ADR（対応フロー設計判断） | `.md` | `project/50_decision_log/` |

### チェックリスト（Phase 3 -> Phase 4 ゲート）

- [ ] インシデント宣言基準を定義した（2 チーム関与 / 顧客可視 / 1h 未解決）
- [ ] ICS 4 役割（IC, Ops, Comms, Planning）の担当者リストを作成した
- [ ] インシデント状態ドキュメントのテンプレートを準備した
- [ ] 3 パターン以上のプレイブック（テスト/変更/プロセス誘発型）を作成した
- [ ] カスケード障害対策（負荷制限、縮退運転、リトライ戦略）を設計した
- [ ] ハンドオフ手順を文書化した
- [ ] 訓練計画（Wheel of Misfortune / DiRT / ゲームデー）を策定した

### 次工程への引き渡し

```
「incident-response スキルでポストモーテムテンプレートを作って」
「review スキルで運用設計成果物を総合レビューして」
```

---

## Phase 4: ポストモーテム・継続改善

### 概要

非難なしポストモーテム文化を構築し、インシデントからの学習を組織知として蓄積する仕組みを整備する。全運用設計成果物の品質を総合検証し、継続的な運用改善サイクル（SLO 見直し、プレイブック更新、訓練実施）を定義する。

### 使用スキル

| スキル | 役割 | トリガー例 |
|:---|:---|:---|
| **incident-response** | ポストモーテムテンプレート、非難なし文化導入、レビュープロセス、アクションアイテム追跡 | 「ポストモーテムのテンプレートを作って」「非難なし文化を導入したい」 |
| **review** | 運用設計成果物の品質レビュー（SLO 定義、プレイブック、対応フロー） | 「運用設計をレビューして」「プレイブックの品質を確認して」 |
| **data-validation** | SLO メトリクス・エラーバジェット消費率・インシデント統計の数値検証 | 「SLO の達成率を検証して」「インシデント統計を検証して」 |
| **diagram**（補助） | 改善後のアーキテクチャ図更新 | 「構成図を最新化して」 |
| **drm**（補助） | インシデントレビュー会議の DRM アジェンダ生成 | 「インシデントレビュー会議を準備して」 |

### ポストモーテム文化の構築

```
インシデント解決
  |
  v
ポストモーテム作成（インシデント後 48h 以内）
  ├── 5 Whys で根本原因を深掘り
  ├── Action Items を Type 分類（prevent / mitigate / process）
  └── Lessons Learned（What went well / wrong / lucky）
  |
  v
シニアレビュー
  ├── データ完全性の確認
  ├── 影響評価の妥当性検証
  ├── 根本原因分析の深さ確認
  └── アクションプランの実行可能性検証
  |
  v
チーム共有 --> 組織全体公開
  ├── Postmortem of the Month（月次ニュースレター）
  └── 読書会（過去のポストモーテムの議論）
  |
  v
アクションアイテム追跡
  └── 完了追跡を義務化、四半期レビュー
```

### 継続改善サイクル

| 頻度 | アクション | 使用スキル |
|:---|:---|:---|
| 週次 | エラーバジェット消費率の確認、アクションアイテム進捗確認 | data-validation |
| 月次 | SLO 達成率レポート、ポストモーテム読書会 | incident-response + review |
| 四半期 | SLO 目標値の見直し、プレイブック更新、訓練実施 | incident-response + observability |
| 年次 | OMM 再評価、DiRT（災害復旧訓練）実施 | observability + incident-response |

### 成果物

| 成果物 | 形式 | 配置先 |
|:---|:---|:---|
| ポストモーテムテンプレート | `.md` | `docs/operations/templates/postmortem.md` |
| 非難なし文化導入ガイド | `.md` | `docs/operations/blameless-culture-guide.md` |
| 運用設計レビューレポート | `.md` | `docs/reviews/` |
| 数値検証レポート（SLO 達成率、エラーバジェット） | `.md` | `docs/reviews/` |
| 継続改善サイクル定義書 | `.md` | `docs/operations/improvement-cycle.md` |
| ADR（改善施策の判断記録） | `.md` | `project/50_decision_log/` |

### チェックリスト（Phase 4 完了条件）

- [ ] ポストモーテムテンプレート（5 Whys, Action Items, Lessons Learned）を準備した
- [ ] 非難なし原則をドキュメント化しチームに周知した
- [ ] レビュープロセス（作成 -> シニアレビュー -> 共有）を定義した
- [ ] review で全運用設計成果物の Critical/Major = 0
- [ ] SLO メトリクス・エラーバジェット消費率が data-validation で検証済み
- [ ] 継続改善サイクル（週次/月次/四半期/年次）が定義されている
- [ ] アクションアイテム追跡の仕組みを構築した
- [ ] 全 ADR 記録が project/50_decision_log/ に完備されている

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| Phase 0 で SLO が現実離れしている | 現行パフォーマンスからの逆算 or ビジネス不在 | ビジネスオーナーと共同で SLO を再設定。内部 SLO は外部より厳しくする |
| Phase 0 で OMM 評価の合意が得られない | ステークホルダー間の認識差 | 具体的なメトリクス（MTTR、デプロイ頻度等）を提示して客観的に議論 |
| Phase 1 でイベントのカーディナリティが低い | 一意識別子（user_id 等）を含めていない | 高カーディナリティフィールドを 10 個以上追加 |
| Phase 1 でトレースが不完全 | コンテキスト伝搬の欠落 | サービス間ヘッダ伝搬（W3C TraceContext）を全経路で確認 |
| Phase 1 でテレメトリコストが急増 | 全イベント 100% 保存 | サンプリング戦略を導入し、ターゲットレートを設定 |
| Phase 2 でアラートが多すぎて対応しきれない | 非アクショナブルアラートが混在 | 各アラートが 4 基準を満たすか再評価し、SLO ベースに移行 |
| Phase 2 でオンコールのバーンアウト | チーム規模不足、アラートノイズ | 最低 8 名への増員、アラート最適化を検討 |
| Phase 2 で SLO アラートがフラッピング | ベースラインウィンドウが小さすぎる | 4 倍ルール（1h ベース -> 4h 予測）を遵守 |
| Phase 3 でインシデント対応が属人化 | 手順が文書化されていない | プレイブック作成 + Wheel of Misfortune 訓練 |
| Phase 3 でカスケード障害が止まらない | 負荷制限・リトライ戦略の未実装 | 負荷テスト + 指数バックオフ + リトライバジェット実装 |
| Phase 4 でポストモーテムが形骸化 | 非難の文化、アクションアイテム未追跡 | 非難なし原則の再徹底、追跡ツールの導入 |
| Phase 4 でエラーバジェットが常に枯渇 | SLO が厳しすぎる or 根本的な品質問題 | SLO の緩和を検討、または信頼性投資を増加 |
| Phase 3 -> Phase 2 の差し戻しが繰り返される | 監視設計が不十分 | Phase 0 に戻り SLI/SLO を再評価、計測ポイントを追加 |

---

## スキル発動マトリクス（全フェーズ x 全スキル）

| スキル | Ph.0 | Ph.1 | Ph.2 | Ph.3 | Ph.4 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **incident-response** | **主** | - | **主** | **主** | **主** |
| **observability** | **主** | **主** | **主** | - | **補** |
| **diagram** | - | **主** | **補** | **補** | **補** |
| **review** | - | - | **補** | **補** | **主** |
| **data-validation** | - | **補** | **補** | - | **主** |
| **distill** | **補** | - | - | - | - |
| **pdf-convert** | **補** | - | - | - | - |
| **drm** | - | - | - | - | **補** |
| **cicd-design** _(将来)_ | - | - | - | - | - |

**凡例**: **主** = フェーズの主要スキル、**補** = 補助的に使用、- = 不使用

> **Note**: `cicd-design` スキルは未作成。将来的に Phase 1（パイプライン設計）や Phase 2（デプロイ戦略と監視の統合）に統合予定。

---

## スキル間連携図

```
Phase 0: 運用要件インテーク
+-------------------------------------+
| incident-response                    |
|   +-- SLI/SLO 設計                  |
|   +-- エラーバジェットポリシー       |
| observability                        |
|   +-- OMM 成熟度評価                |
| (+ distill: 運用ドキュメント蒸留)    |
+-----------------+-------------------+
                  | SLO 定義 + 成熟度評価
                  v
Phase 1: オブザーバビリティ基盤設計
+-------------------------------------+
| observability                        |
|   +-- 構造化イベント設計             |
|   +-- 分散トレーシング設計           |
|   +-- OTel 計装戦略                  |
|   +-- サンプリング戦略               |
|   +-- テレメトリパイプライン設計     |
| diagram <-- パイプラインアーキテクチャ|
+-----------------+-------------------+
                  | 計装・パイプライン設計
                  v
Phase 2: 監視・アラート体制構築
+-------------------------------------+
| observability                        |
|   +-- SLO ベースアラート             |
|   +-- 予測バーンアラート             |
| incident-response                    |
|   +-- Four Golden Signals            |
|   +-- オンコール体制                 |
|   +-- エスカレーションパス           |
| diagram <-- 監視構成図               |
+-----------------+-------------------+
                  |     ^
                  |     | 監視不備の検出時
                  v     |
Phase 3: インシデント対応プロセス構築
+-------------------------------------+
| incident-response                    |
|   +-- ICS 役割分担                   |
|   +-- インシデント対応フロー         |
|   +-- プレイブック                   |
|   +-- カスケード障害対策             |
|   +-- 訓練設計                       |
| diagram <-- 対応フロー図             |
+-----------------+-------------------+
                  |     ^
                  |     | 改善フィードバック
                  v     |
Phase 4: ポストモーテム・継続改善
+-------------------------------------+
| incident-response                    |
|   +-- ポストモーテム文化             |
|   +-- アクションアイテム追跡         |
| review (Critical/Major = 0)          |
| data-validation (SLO 数値検証)       |
| --> 継続改善サイクル定義             |
| --> ADR 記録完備                     |
+-------------------------------------+
```

---

## ディレクトリ構造テンプレート

```
<project-root>/
+-- project/
|   +-- 10_inbox/                  <-- Phase 0: 運用ドキュメント（Markdown 化済み）
|   +-- 20_notes/                  <-- Phase 0: 蒸留済み運用要件
|   |   +-- operational-requirements.md
|   +-- 50_decision_log/           <-- Phase 0-4: ADR（設計判断記録）
|   |   +-- ADR-0001-*.md
|   |   +-- ...
|   +-- 90_references/             <-- 外部参照資料
|   +-- 00_schemas/                <-- ドキュメントスキーマ定義
+-- docs/
|   +-- operations/           <-- Phase 0-4: 運用設計ドキュメント
|   |   +-- slo-definition.md         SLI/SLO 定義書
|   |   +-- error-budget-policy.md    エラーバジェットポリシー
|   |   +-- omm-assessment.md         OMM 成熟度評価
|   |   +-- improvement-roadmap.md    改善ロードマップ
|   |   +-- event-design.md           構造化イベント設計
|   |   +-- tracing-design.md         分散トレーシング設計
|   |   +-- otel-instrumentation.md   OTel 計装ガイド
|   |   +-- sampling-strategy.md      サンプリング戦略
|   |   +-- telemetry-pipeline.md     テレメトリパイプライン設計
|   |   +-- monitoring-design.md      Four Golden Signals 監視設計
|   |   +-- slo-alerting.md           SLO ベースアラート設計
|   |   +-- on-call-design.md         オンコール体制設計
|   |   +-- dashboard-design.md       ダッシュボード設計
|   |   +-- incident-response-guide.md  インシデント対応ガイド
|   |   +-- cascade-failure-mitigation.md カスケード障害対策
|   |   +-- training-plan.md          訓練計画
|   |   +-- blameless-culture-guide.md  非難なし文化導入ガイド
|   |   +-- improvement-cycle.md      継続改善サイクル定義
|   |   +-- templates/                テンプレート類
|   |   |   +-- incident-status.md      インシデント状態ドキュメント
|   |   |   +-- postmortem.md           ポストモーテム
|   |   +-- playbooks/                プレイブック
|   |       +-- test-induced.md         テスト誘発型
|   |       +-- change-induced.md       変更誘発型
|   |       +-- process-induced.md      プロセス誘発型
|   +-- diagrams/             <-- Phase 1-4: 構成図
|   |   +-- telemetry-pipeline.drawio
|   |   +-- monitoring-architecture.drawio
|   |   +-- incident-response-flow.drawio
|   |   +-- escalation-flow.drawio
|   +-- reviews/              <-- Phase 4: レビューレポート
+-- .agents/
|   +-- skills/                  導入済みスキル群
|   +-- workflows/               ワークフロー定義
+-- CLAUDE.md                 <-- プロジェクト設定
```

---

## クイックスタート: 典型的な運用設計の進め方

### パターン A: 新規サービス運用設計（フルパイプライン）

```
1. 「SLO を設計して」                               --> incident-response (Step 1)
2. 「オブザーバビリティ成熟度を評価して」            --> observability (Step 1)
3. 「構造化イベントを設計して」                      --> observability (Step 2)
4. 「OTel 計装を設計して」                           --> observability (Step 4)
5. 「テレメトリパイプラインを設計して」              --> observability (Step 7)
6. 「パイプライン構成図を描いて」                    --> diagram
7. 「SLO ベースアラートを設計して」                  --> observability (Step 5)
8. 「Four Golden Signals の監視を設計して」          --> incident-response (Step 2)
9. 「オンコール体制を設計して」                      --> incident-response (Step 3)
10. 「インシデント対応フローを設計して」             --> incident-response (Step 4)
11. 「プレイブックを作成して」                       --> incident-response (Step 7)
12. 「ポストモーテムテンプレートを作成して」         --> incident-response (Step 6)
13. 「運用設計をレビューして」                       --> review
14. 「SLO の数値を検証して」                         --> data-validation
```

### パターン B: 既存システムの監視強化（Phase 1 -> Phase 2 中心）

```
1. 「現在のオブザーバビリティ成熟度を評価して」      --> observability (Step 1)
2. 「構造化イベントに移行したい」                    --> observability (Step 2)
3. 「OTel の自動計装を導入したい」                   --> observability (Step 4)
4. 「サンプリング戦略を決めたい」                    --> observability (Step 6)
5. 「SLO ベースアラートに移行したい」                --> observability (Step 5)
6. 「アラート疲れを解消したい」                      --> incident-response (Step 2)
7. 「監視構成図を描いて」                            --> diagram
8. 「監視設計をレビューして」                        --> review
```

### パターン C: インシデント対応体制の立ち上げ（Phase 3 -> Phase 4 中心）

```
1. 「SLO とエラーバジェットを確認して」              --> incident-response (Step 1)
2. 「インシデント対応フローを設計して」              --> incident-response (Step 4)
3. 「ICS の役割分担を定義して」                      --> incident-response (Step 4)
4. 「プレイブックを作成して」                        --> incident-response (Step 7)
5. 「オンコール体制を設計して」                      --> incident-response (Step 3)
6. 「ポストモーテムの文化を導入したい」              --> incident-response (Step 6)
7. 「訓練計画を策定して」                            --> incident-response (Step 3d)
8. 「対応フローをレビューして」                      --> review
```

### パターン D: モニタリング -> オブザーバビリティ移行（段階的移行）

```
1. 「現在のモニタリング状況を棚卸ししたい」          --> observability (Step 1)
2. 「SLI/SLO を定義して」                            --> incident-response (Step 1)
3. 「既存ログを構造化イベントに再設計して」          --> observability (Step 2)
4. 「OTel 計装を段階的に導入したい」                 --> observability (Step 4)
5. 「テレメトリパイプラインを設計して」              --> observability (Step 7)
6. 「SLO ベースアラートに段階的に移行したい」        --> observability (Step 5)
7. 「既存アラート 200 件を整理したい」               --> observability (Step 5d)
8. 「移行の数値目標を検証して」                      --> data-validation
```

---

## 関連ワークフロー

| ワークフロー | 関係 |
|:---|:---|
| [engineering-workflow.md](engineering-workflow.md) | 開発ワークフロー Phase 4（リリース）と本ワークフロー Phase 2-3（監視・インシデント対応）が接続。リリース後の運用体制を本ワークフローで構築する |
| [architecture-design-workflow.md](architecture-design-workflow.md) | アーキテクチャ設計の非機能要件（可用性、パフォーマンス）が本ワークフロー Phase 0 の SLO 設計にインプットされる |
| [bd-skills-workflow.md](bd-skills-workflow.md) | BD 案件の技術提案に運用設計（SLO、監視体制）を含める場合に併用 |
| [proposal-lifecycle.md](proposal-lifecycle.md) | 提案書に運用設計セクション（SLO、インシデント対応体制）を含める場合に参照 |
| [convert-pdf.md](convert-pdf.md) | 既存運用マニュアルの PDF -> Markdown 変換手順 |
