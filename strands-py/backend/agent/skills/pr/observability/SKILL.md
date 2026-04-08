---
name: observability
description: >
  オブザーバビリティエンジニアリングの実践を包括的に支援する。構造化イベント設計、
  分散トレーシング、OpenTelemetry 計装、SLO ベースアラート、サンプリング戦略、
  テレメトリパイプライン構築、成熟度評価を一気通貫でガイドする。
  Use when user says「オブザーバビリティを導入したい」「OpenTelemetryの計装を設計して」
  「SLOベースのアラートを設計して」「テレメトリパイプラインを構築したい」
  「分散トレーシングを導入して」「監視からオブザーバビリティに移行したい」
  「構造化イベントを設計して」「サンプリング戦略を決めたい」「オブザーバビリティ成熟度を評価して」
  「ログが多すぎる」「デバッグが辛い」「アラートの嵐」「何が起きてるか分からない」。
  Do NOT use for: インフラ基盤のメトリクス監視設定（→ 既存モニタリングツール）、
  単純なログ集約設定（→ ロギングツール設定タスク）、
  インシデント対応フロー・オンコール体制設計・ポストモーテム（→ incident-response）。
metadata:
  author: KC-Prop-Foundry
  version: 1.1.0
  category: quality-assurance
  pattern: "sequential"
  based-on: "Observability Engineering (Charity Majors, Liz Fong-Jones, George Miranda, O'Reilly 2022)"
---

# Skill: Observability Engineering（オブザーバビリティ設計・導入）

> **「システムがどんな状態に陥っても、新規コードなしに理解・説明できる力を組織に実装する」**

## strands-py / Strands Agent での利用

設計書・OTel 案・SLO 定義は **`file_read` / `file_write`** とプロジェクト workspace（`notes` / `proposal` 等）を正とする。references の YAML はクラスタ適用の例示。incident-response・diagram との分担は [references/strands-py-runtime.md](references/strands-py-runtime.md) を参照。

## Instructions

### ワークフロー内の位置

```
要件定義 → [observability] → 計装実装 → 運用開始
                 ↓
  成熟度評価 / イベント設計 / トレーシング設計 /
  OTel 計装設計 / SLO アラート設計 /
  サンプリング戦略 / テレメトリパイプライン設計
```

### 入力

| 入力 | 説明 | 例 |
|:---|:---|:---|
| 対象システムの概要 | アーキテクチャ、サービス構成、使用言語 | マイクロサービス 12個、Go/Python、K8s 上 |
| 現状のモニタリング状況 | 既存ツール、アラート設定、課題 | Prometheus + Grafana、アラート 200件で疲弊 |
| ビジネス要件 | SLA/SLO ターゲット、重要なユーザージャーニー | 99.95% 可用性、決済フロー < 500ms |

### 出力

| 出力 | 形式 | 説明 |
|:---|:---|:---|
| オブザーバビリティ設計書 | Markdown | 各ステップの設計成果をまとめた文書 |
| OTel 計装ガイド | Markdown + Code | 自動計装・カスタム計装の具体的コード |
| SLO 定義書 | Markdown | SLI/SLO/エラーバジェットの定義 |
| テレメトリパイプライン設計図 | Markdown / draw.io | パイプラインアーキテクチャ |

---

## Step 1: オブザーバビリティ成熟度評価（OMM）

組織の現状を OMM（Observability Maturity Model）の 5 能力で診断する。

### 1a. 5 能力の現状評価

各能力を「未着手 / 初期 / 発展 / 成熟」の 4 段階で評価する。

| 能力 | 評価観点 |
|:---|:---|
| **障害への回復力** | MTTR、アラート疲れの有無、オンコール持続可能性 |
| **高品質コードの提供** | 本番バグ頻度、デプロイへの恐怖感、デバッグの容易さ |
| **技術的負債の管理** | コアビジネス作業の割合、反復作業の多寡 |
| **リリースケイデンス** | コミット→本番の所要時間、フィーチャーフラグ活用度 |
| **ユーザー行動の理解** | PM のデータアクセス度、顧客フィードバックの速度 |

### 1b. 優先能力の特定

ビジネスインパクトが最大の能力を特定し、投資優先順位を決定する。

**チェックリスト**:
- [ ] 5 能力すべてを 4 段階で評価した
- [ ] ビジネスインパクト順に優先順位を付けた
- [ ] 現状の主要課題（アラート疲れ、デバッグ困難等）を明文化した
- [ ] ステークホルダーの合意を得た

---

## Step 2: 構造化イベント設計

オブザーバビリティの基本単位である「任意幅の構造化イベント」を設計する。

### 2a. イベントスコープの定義

- 1 イベント = 1 サービスにおける 1 リクエストの処理全体
- リクエスト開始時に空マップを初期化し、処理中にコンテキストを蓄積

### 2b. フィールド設計

**必須フィールド**:
- リクエスト識別: `trace_id`, `span_id`, `parent_id`
- タイミング: `timestamp`, `duration_ms`
- サービス: `service_name`, `span_name`
- 結果: `status_code`, `error_message`

**高カーディナリティフィールド**（デバッグに最も有用）:
- `user_id`, `session_id`, `request_id`, `shopping_cart_id`
- `build_id`, `hostname`, `instance_type`, `availability_zone`

**ビジネスコンテキストフィールド**:
- `app.api_key`, `app.dataset.id`, `app.team.id`
- `app.raw_size_bytes`, `app.sample_rate`

### 2c. 既存ログからの移行パス

1. 非構造化ログ → 構造化ログ（JSON 形式）
2. 複数行ログ → 1 作業単位 = 1 イベントに統合
3. request_id 等の相関フィールドを追加
4. トレーシングフィールドを追加

**チェックリスト**:
- [ ] イベントのスコープ（1リクエスト/1サービス）を定義した
- [ ] 高カーディナリティフィールドを 10 個以上設計した
- [ ] ビジネスロジック固有のフィールドを含めた
- [ ] フィールド数の上限を設けていない（任意幅）
- [ ] 既存ログからの移行パスを検討した

---

## Step 3: 分散トレーシング設計

イベントをトレースとしてステッチし、サービス間の関係を可視化する。

### 3a. スパン構造の設計

```
Root Span (API Gateway)
├── Child Span (Auth Service)
├── Child Span (User Service)
│   └── Child Span (Database Query)
└── Child Span (Notification Service)
```

- 各スパンに 5 つの必須フィールド: Trace ID, Span ID, Parent ID, Timestamp, Duration
- Service Name と Span Name で作業内容を識別

### 3b. トレースコンテキスト伝搬

- **標準**: W3C TraceContext（推奨）または B3
- HTTP ヘッダで Trace ID と Parent Span ID を伝搬
- gRPC メタデータでも同様に伝搬

### 3c. カスタムスパンの追加

- CPU 集中処理の「ホットブロック」を個別スパンに分離
- バッチジョブの各チャンクにスパンを付与
- 非分散（モノリシック）コードでもトレーシングを活用

**チェックリスト**:
- [ ] サービス間のスパン親子関係を図示した
- [ ] トレースコンテキスト伝搬の標準を選択した（W3C / B3）
- [ ] クリティカルパスのカスタムスパンを特定した
- [ ] 非同期処理・バッチジョブのトレーシング方針を決定した

---

## Step 4: OpenTelemetry 計装設計

OTel を使った 3 段階計装戦略を設計する。

### 4a. 自動計装の導入

- HTTP/gRPC フレームワーク統合で即座にスパン生成
- DB/Cache クライアントの自動計装でダウンストリーム可視化
- 言語ごとの導入方法:
  - **Go**: ラッパー/インターセプター（`otelhttp`, `otelgrpc`）
  - **Java/.NET**: ランタイムエージェントの自動登録
  - **Python**: `opentelemetry-instrument` CLI

### 4b. カスタム計装の追加

- スパン属性にビジネスロジックフィールドを追加
- パッケージ単位でトレーサーを定義: `var tr = otel.Tracer("module_name")`
- スパンの開始/終了を明示的に管理

```go
// Example: custom span with business attributes
func processOrder(ctx context.Context, order Order) error {
    ctx, sp := tr.Start(ctx, "process_order")
    defer sp.End()

    sp.SetAttributes(
        attribute.String("order.id", order.ID),
        attribute.Float64("order.total", order.Total),
        attribute.String("order.customer_id", order.CustomerID),
    )
    // ... business logic ...
    return nil
}
```

### 4c. バックエンド連携

- **推奨**: OTLP gRPC エクスポーター → OTel Collector → バックエンド
- 直接エクスポートも可能だが、Collector 経由が柔軟
- 移行期は複数エクスポーターで既存/新規ツールへ同時送信

**チェックリスト**:
- [ ] 自動計装の対象フレームワークを特定した
- [ ] カスタム計装の優先順位（クリティカルパス優先）を決めた
- [ ] ビジネスロジック固有の属性を計装に組み込んだ
- [ ] エクスポート先（Collector / 直接）を決定した
- [ ] 言語ごとの OTel SDK バージョンを確認した

---

## Step 5: SLO ベースアラート設計

閾値アラートから SLO ベースアラートへ移行し、アラート疲れを解消する。

### 5a. SLI の定義（イベントベース）

各クリティカルユーザージャーニーに対して SLI を定義する。

```yaml
# Example SLI definition
sli:
  name: "home_page_load"
  description: "User can load home page quickly"
  qualifying_event:
    filter: "request.path == '/home'"
  good_event:
    condition: "duration_ms < 100 AND status_code < 400"
  bad_event:
    condition: "duration_ms >= 100 OR status_code >= 400"
```

### 5b. SLO ターゲットとエラーバジェット

- SLO ターゲット設定（例: 99.9% → 月間 43分50秒のダウンタイム許容）
- **30 日スライディングウィンドウ推奨**（固定ウィンドウは顧客感情と不一致）
- エラーバジェット = 許容失敗リクエスト数

### 5c. 予測バーンアラートの設計

- **短期アラート**: 1時間ベースライン → 4時間予測（即時対応用、ページング）
- **長期アラート**: 6時間ベースライン → 24時間予測（スプリント計画用、通知）
- **比例外挿**: 失敗率（%）をトラフィック量で調整（線形外挿より正確）
- 両方のタイムスケールで測定し、どちらかがトリガーしたらアクション

### 5d. 既存アラートの整理

- 2 基準を満たさないアラートを削除:
  1. ユーザー体験劣化の信頼できるインジケーターであること
  2. アクション可能であること
- SLO ベースアラートの信頼性が実証されてから段階的に移行

**チェックリスト**:
- [ ] クリティカルユーザージャーニーごとに SLI を定義した
- [ ] イベントベース（時間ベースではなく）の SLI を採用した
- [ ] 30 日スライディングウィンドウの SLO を設定した
- [ ] 短期・長期の予測バーンアラートを設計した
- [ ] 比例外挿を使用して予測精度を高めた
- [ ] 既存の不要アラートの削除計画を策定した

---

## Step 6: サンプリング戦略設計

コスト最適化とデータ忠実性を両立するサンプリング戦略を設計する。

### 6a. サンプリング要件の評価

| 要素 | 評価 |
|:---|:---|
| トラフィック量 | 秒間リクエスト数、日次イベント総数 |
| トラフィック均質性 | 大半が同一パターンか、多様なパターンか |
| エラー率 | エラーの頻度と種類の多様性 |
| コスト制約 | バックエンドのストレージ/クエリコスト |

### 6b. 戦略の選択

- **小規模（< 10K events/sec）**: 全イベント保存 or 固定率サンプリング
- **中規模（10K-100K events/sec）**: キーベース動的サンプリング
- **大規模（> 100K events/sec）**: キー×履歴の組合せ + ターゲットレートサンプリング

### 6c. Head/Tail サンプリングの決定

- **Head**: 静的フィールド（customer_id, endpoint）で判断。全スパン捕捉保証
- **Tail**: 動的フィールド（error, latency）で判断。バッファリング必要
- **併用推奨**: Head で基本サンプリング、Tail でエラー/外れ値を確実に捕捉

### 6d. サンプルレートの記録

- 各イベントにサンプルレートを記録 → バックエンドでの正確な再構成
- 加重アルゴリズムで COUNT, SUM, PERCENTILE を正確に計算

**チェックリスト**:
- [ ] トラフィック量と特性を評価した
- [ ] サンプリング戦略を選択した（固定率/動的/キーベース/組合せ）
- [ ] Head/Tail サンプリングの方針を決定した
- [ ] サンプルレートのイベント内記録を設計した
- [ ] エラーイベントが確実に捕捉される設計になっている

---

## Step 7: テレメトリパイプライン設計

テレメトリデータのルーティング・処理・品質管理のパイプラインを設計する。

### 7a. パイプライン要件の整理

- データソース: アプリケーション（traces, logs, metrics）
- バックエンド: 分析ツール、長期保存、リアルタイムダッシュボード
- セキュリティ: PII マスキング、コンプライアンス要件
- 可用性: バックエンド障害時のバッファリング要件

### 7b. アーキテクチャ設計

```
Applications
  ├── OTel SDK (auto + custom instrumentation)
  │     ↓ OTLP
  ├── OTel Collector (Agent mode, per-node sidecar)
  │     ↓ OTLP
  └── OTel Collector (Gateway mode, centralized)
        ├── → Tracing Backend (Jaeger, Honeycomb, etc.)
        ├── → Metrics Backend (Prometheus, etc.)
        ├── → Logging Backend (Elasticsearch, etc.)
        └── → Data Warehouse (S3 → Presto, etc.)
```

### 7c. パイプラインコンポーネント設計

| コンポーネント | 推奨ツール | 役割 |
|:---|:---|:---|
| Receiver | OTel Collector | OTLP/Zipkin/Jaeger 形式でデータ受信 |
| Buffer | Kafka / Amazon Kinesis | バックエンド障害時のデータバッファリング |
| Processor | OTel Collector Processor | フィルタリング、サンプリング、メタデータ付加 |
| Exporter | OTel Collector Exporter | 各バックエンドへのデータ送信 |

### 7d. データ品質管理

- タイムスタンプの異常検出と補正
- PII の自動検出・マスキング
- スキーマ検証（期待されるフィールドの存在・型チェック）
- 低価値データのフィルタリング
- 合成データによるパイプライン鮮度監視

**チェックリスト**:
- [ ] データソースとバックエンドのマッピングを定義した
- [ ] OTel Collector の Agent/Gateway 構成を設計した
- [ ] バッファリング戦略（Kafka 等）を決定した
- [ ] PII マスキング/コンプライアンス要件を反映した
- [ ] データ品質チェックポイントを設計した
- [ ] パイプライン自体のモニタリング方針を策定した

### 7e. オブザーバビリティ設計 Slop 防止チェック

LLM が生成するオブザーバビリティ設計は **Distributional Convergence（分布的収束）** により、
どのサービスにも同じ計装・同じアラート・同じダッシュボードを出力しがちになる。
以下のパターンに該当する出力は「slop（汎用的すぎるAI出力）」として検出・修正する。

| ID | パターン名 | 症状 | 対策 |
|:---|:---|:---|:---|
| OB-1 | コピペ計装症候群 | サービスの種類（API / Worker / Batch / Streaming）に関係なく同一のスパン構造・属性セットを出力する | サービスの通信パターン・処理特性に応じてスパン粒度とカスタム属性を個別設計する。API は HTTP 属性、Worker はジョブ属性、Batch はチャンク属性を持つ |
| OB-2 | 均一閾値アラート | すべての SLO に同じターゲット（99.9%）・同じバーンレートウィンドウ（1h/6h）を適用する | サービスの重要度・トラフィック特性・ビジネスインパクトに応じてターゲットとウィンドウを個別設定する。決済は 99.99%、内部ツールは 99.5% など |
| OB-3 | RED/USE テンプレートダッシュボード | すべてのサービスに Request Rate / Error Rate / Duration + Utilization / Saturation / Errors の同一レイアウトを適用する | サービスの役割に応じてダッシュボードを設計する。API は SLI バーンダウン、Worker はキュー深度・処理レイテンシ、DB はクエリプラン・ロック競合を中心に構成 |
| OB-4 | 一律サンプリング戦略 | 全エンドポイントに同一のサンプリングレート（例: 10%）を適用する | エンドポイントの重要度・トラフィック量・エラー率に基づいてキーベースの動的サンプリングを設計する。高頻度正常リクエストは低レート、エラー・高レイテンシは 100% 捕捉 |
| OB-5 | 汎用キーバリューログスキーマ | `key=value` ペアの羅列で、ドメイン固有のセマンティクスを持たないログ/イベントスキーマを出力する | ビジネスドメインのエンティティ（注文、ユーザー、トランザクション）をファーストクラスのフィールドとして設計し、高カーディナリティフィールドに意味的な名前を付ける |
| OB-6 | 三本柱均等テレメトリ設計 | Logs / Metrics / Traces を常に同じ比重で設計し、サービス特性に関係なく三本柱を均等に導入する | サービスの可観測性ニーズに応じて柱の比重を調整する。リクエスト駆動サービスは Traces 重視、バッチは Metrics + Logs 重視、イベント駆動は Traces + Structured Events 重視 |

> **コア原則**: オブザーバビリティ設計はシステムの「神経系統」であり、汎用の「健康診断キット」ではない。
> **セルフテスト**: 生成した計装・アラート・ダッシュボード設計からサービス名を消して別のサービスに貼り付けても違和感がなければ、それは slop である。

**チェックリスト（Slop 防止）**:
- [ ] OB-1〜OB-6 のパターンに該当する出力がないか確認した
- [ ] サービス名を伏せても成立する汎用設計になっていないか検証した

---

## Examples

### Example 1: モニタリング → オブザーバビリティ移行

```
「Prometheus + Grafana でアラート 200 件、アラート疲れがひどい。オブザーバビリティに移行したい」

→ Step 1 で OMM 5 能力を評価。障害回復力が「未着手」レベルと判定
→ Step 2 で既存ログを構造化イベントに再設計（JSON 形式、request_id 追加）
→ Step 4 で OTel 自動計装を最優先サービス 3 つに導入
→ Step 5 で SLO ベースアラートを設計、200 件のアラートを 5 つの SLO に統合
→ 成果物: 移行ロードマップ、SLO 定義書、OTel 計装ガイド
```

### Example 2: OpenTelemetry 計装設計

```
「Go マイクロサービス 12 個に OpenTelemetry を導入したい」

→ Step 4a で otelhttp/otelgrpc の自動計装を全サービスに適用
→ Step 4b でクリティカルパス（決済フロー）にカスタムスパンと属性を追加
→ Step 4c で OTel Collector → Jaeger + Prometheus のパイプラインを構成
→ Step 3 で W3C TraceContext によるコンテキスト伝搬を設計
→ 成果物: 計装ガイド（Go コード付き）、Collector 設定ファイル
```

### Example 3: SLO アラート設計

```
「決済サービスの SLO を 99.95% に設定し、予測バーンアラートを導入したい」

→ Step 5a で決済フローの SLI 定義（イベントベース: duration < 500ms AND status < 400）
→ Step 5b で 30 日スライディングウィンドウ、エラーバジェット計算
→ Step 5c で短期（1h→4h）と長期（6h→24h）の予測バーンアラートを設計
→ Step 5d で既存閾値アラートの削除計画を策定
→ 成果物: SLO 定義書、バーンアラート設計書、移行計画
```

### Example 4: テレメトリパイプライン構築

```
「月間 10 億イベントを処理するテレメトリパイプラインを設計したい」

→ Step 6 でキー×履歴の動的サンプリング戦略を設計（Head + Tail 併用）
→ Step 7b で OTel Collector (Agent + Gateway) + Kafka バッファの構成を設計
→ Step 7c で PII マスキング、メタデータ付加、低価値データフィルタリングを設計
→ Step 7d で合成データによるパイプライン鮮度監視を設計
→ 成果物: パイプラインアーキテクチャ図、Collector 設定、サンプリング設計書
```

### Example 5: オブザーバビリティ成熟度評価の実施

```
「チームのオブザーバビリティ成熟度を評価して、半年の改善ロードマップを作りたい」

→ Step 1a で OMM 5 能力を 4 段階評価:
  - 障害への回復力: 初期（MTTR 8h、アラート疲れあり、プレイブックなし）
  - 高品質コードの提供: 未着手（本番デバッグ不可、ログ頼み）
  - 技術的負債の管理: 初期（コアビジネス作業 40%）
  - リリースケイデンス: 発展（週次リリース、CI/CD 整備済み）
  - ユーザー行動の理解: 未着手（PM がデータにアクセスできない）
→ Step 1b でビジネスインパクト順に優先:
  1. 障害への回復力（MTTR 直結 = 収益影響最大）
  2. 高品質コードの提供（開発速度のボトルネック）
→ 改善ロードマップ策定:
  - Month 1-3: OTel 自動計装 + SLO 2 個定義 + バーンアラート導入
  - Month 4-6: 全サービス計装 + ODD 文化トレーニング + PM ダッシュボード整備
→ 成果物: OMM 評価レポート、6 ヶ月改善ロードマップ、KPI ダッシュボード設計
```

### Example 6: サンプリング戦略の設計

```
「秒間 50K イベント、テレメトリコストが月 300 万円。半減したい」

→ Step 6a で要件評価:
  - トラフィック: 50K events/sec（中〜大規模）
  - 均質性: 80% が /api/v1/products（高頻度・低多様性）
  - エラー率: 0.1%（低頻度だが見逃し不可）
  - コスト目標: 月 150 万円（50% 削減）
→ Step 6b でキーベース動的サンプリングを選択:
  - キー: http.route × status_code
  - /api/v1/products (正常): 5% サンプリング
  - /api/v1/payments (全量): 100% 保存
  - 全エンドポイント (エラー): 100% 保存
→ Step 6c で Head + Tail 併用設計:
  - Head: http.route ベースの動的レート
  - Tail: status_code=ERROR と duration_ms > 1000ms を 100% 捕捉
→ Step 6d でサンプルレート記録 → 加重集計の正確性を保証
→ 成果物: サンプリング戦略設計書、OTel Collector 設定、コスト試算シート
```

---

## Troubleshooting

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| イベントのカーディナリティが低い | 一意識別子（user_id 等）を含めていない | Step 2b の高カーディナリティフィールド設計に従い、10 個以上の一意識別子を追加 |
| トレースが不完全 | コンテキスト伝搬の欠落 | Step 3b でサービス間ヘッダ伝搬（W3C TraceContext）を確認・修正 |
| 自動計装で十分なデータが得られない | ビジネスロジックのコンテキスト不足 | Step 4b でカスタム計装を追加し、ビジネス属性をスパンに付与 |
| SLO アラートが頻発 | SLO ターゲットが厳しすぎるか、SLI 定義が不適切 | SLO ターゲットを現実的に調整し、SLI のフィルタ条件を見直す |
| バーンアラートがフラッピング | ベースラインウィンドウが小さすぎる | 4 倍ルール（1h ベース → 4h 予測）を遵守し、ウィンドウサイズを調整 |
| サンプリングでエラーが見逃される | 固定率サンプリングのみ使用 | キーベースサンプリングでエラーイベントの捕捉率を 1/1 に設定 |
| パイプラインのレイテンシが高い | プロセッサの処理コスト or バッファ飽和 | ボトルネック特定 → スケールアウト or フィルタリング強化 |
| テレメトリコストが急増 | 全イベント 100% 保存 | Step 6 のサンプリング戦略を導入し、ターゲットレートを設定 |
| チームが SLO アラートを信頼しない | 従来の閾値アラートとの併用期間が不足 | 並行運用期間を設け、SLO が先に問題を検知した実績を蓄積 |
| オブザーバビリティが SRE チームに閉じている | 開発者の ODD 文化が未醸成 | Step 1 の OMM 評価で「高品質コードの提供」能力を重点改善 |

---

## References

| ファイル | 内容 |
|:---|:---|
| [omm-evaluation-template.md](references/omm-evaluation-template.md) | OMM 5 能力評価シート（4 段階基準、チェックリスト、総合サマリ、改善ロードマップテンプレート） |
| [otel-collector-configs.md](references/otel-collector-configs.md) | OTel Collector 構成パターン（Agent/Gateway YAML、K8s マニフェスト、移行パターン） |
| [sampling-strategy-decision-flow.md](references/sampling-strategy-decision-flow.md) | サンプリング戦略デシジョンフロー（Head/Tail 比較、OTel 設定例、コスト最適化ガイド） |
| [strands-py-runtime.md](references/strands-py-runtime.md) | strands-py（Strands Agent）上のツール・workspace・YAML 例示の扱い |

## アンチパターン検出

このスキルの出力品質を検証するためのチェックリスト。

- [ ] SLI がイベントベースで定義されているか（リクエストベースの「成功率」だけでなく、品質イベントを含む）
- [ ] OTel Collector の構成が Agent/Gateway パターンのどちらを採用したか根拠があるか
- [ ] サンプリング戦略（Head/Tail）の選定にコスト最適化の観点が含まれているか
- [ ] OMM 5 能力評価の各レベルが具体的な基準で判定されているか（「概ね良い」等の曖昧表現を排除）
- [ ] バーンアラートの設計にバーンレート閾値と対応ウィンドウが数値で定義されているか
- [ ] テレメトリパイプラインのストレージ容量見積もりが具体的に計算されているか

---

## Related Skills

| スキル | 関係 | 説明 |
|:---|:---|:---|
| **diagram** | 出力連携 | テレメトリパイプライン構成図やトレースフロー図の作成 |
| **review** | 品質検証 | オブザーバビリティ設計書・SLO 定義のレビュー |
| **data-validation** | 品質検証 | SLO エラーバジェット計算やサンプリング率の数値検証 |
| **test** | 計装検証 | OTel 計装コードのユニットテスト設計 |
| **data-arch** | 基盤連携 | テレメトリデータのストレージアーキテクチャ選定 |
| **robust-python** | 実装連携 | Python サービスの OTel 計装実装における型安全・エラーハンドリング |
| **effective-typescript** | 実装連携 | TypeScript サービスの OTel 計装実装 |
| **agent-craft** / **agent-craft-strands** | 設計連携（実装） | エージェントへの組み込みは共通。**strands-py** では pr の agent-craft は載らないため、YAML 実装は **dev の agent-craft-strands** |
| **incident-response** | 密接連携 | observability = イベントベース SLI 定義・バーンアラート設計・OTel 計装。incident-response = エラーバジェット運用・インシデント対応プロセス。SLO 設計は observability がイベント品質、incident-response が可用性ポリシーの観点で分担 |
| **project-ops** | 連携 | DORA メトリクスの MTTR 改善に observability の SLO アラート・テレメトリ設計を提供 |
