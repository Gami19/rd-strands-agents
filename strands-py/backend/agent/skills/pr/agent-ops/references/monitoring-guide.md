# エージェント監視ツール統合ガイド

> Source: AI Agents in Action (Micheal Lanham, Manning 2025) Ch.4
> agent-ops スキルの Step 5 の詳細リファレンス

---

## 1. 監視ツール比較

### エージェント専用プラットフォーム

| ツール | 特徴 | 対応フレームワーク | コスト | 適用場面 |
|:---|:---|:---|:---|:---|
| **AgentOps** | エージェント操作に特化した監視 | CrewAI, AutoGen, LangChain, カスタム | フリーミアム | マルチエージェント、CrewAI 中心 |
| **LangSmith** | LangChain エコシステム統合 | LangChain, LangGraph | フリーミアム | LangChain ベースのプロジェクト |
| **LangFuse** | OSS、セルフホスト可能 | 汎用（OpenAI, Anthropic, 他） | OSS / Cloud | プライバシー重視、カスタム統合 |
| **Braintrust** | 評価・監視の統合 | 汎用 | フリーミアム | 評価パイプラインとの統合 |
| **Weights & Biases (Prompts)** | 実験管理と監視の統合 | 汎用 | フリーミアム | ML 実験との統合が必要 |

### 汎用監視プラットフォーム

| ツール | 特徴 | 適用場面 |
|:---|:---|:---|
| **Datadog** | フルスタック監視、LLM Observability | エンタープライズ、既存 Datadog 環境 |
| **Prometheus + Grafana** | OSS メトリクス収集・可視化 | カスタムメトリクス、コスト重視 |
| **AWS CloudWatch** | AWS ネイティブ監視 | AWS 環境でのデプロイ |
| **Azure Monitor** | Azure ネイティブ監視 | Azure 環境でのデプロイ |

### ツール選定フロー

```
CrewAI / AutoGen を使用しているか？
├─ Yes → AgentOps（ネイティブ統合）
└─ No → LangChain を使用しているか？
     ├─ Yes → LangSmith（エコシステム統合）
     └─ No → データのセルフホストが必須か？
          ├─ Yes → LangFuse（OSS セルフホスト）
          └─ No → 既存の監視基盤はあるか？
               ├─ Datadog → Datadog LLM Observability
               ├─ AWS → CloudWatch + カスタムメトリクス
               ├─ Azure → Azure Monitor + AI Studio
               └─ なし → LangFuse Cloud（導入障壁が低い）
```

---

## 2. AgentOps 統合ガイド

書籍 Ch.4 で詳述された AgentOps の統合パターン。

### 2.1 セットアップ

```bash
# Install AgentOps
pip install agentops

# Or with CrewAI integration
pip install crewai[agentops]
```

```python
# .env file
# AGENTOPS_API_KEY="your-api-key"

import agentops
from dotenv import load_dotenv

load_dotenv()
agentops.init()  # Initialize after env vars are loaded
```

### 2.2 収集されるデータ

| データカテゴリ | 内容 | 用途 |
|:---|:---|:---|
| **セッション** | 開始/終了時刻、総時間、ステータス | セッション追跡 |
| **LLM 呼び出し** | プロンプト、応答、モデル名、トークン数 | 品質分析・デバッグ |
| **ツール実行** | ツール名、入力/出力、実行時間 | アクション追跡 |
| **コスト推定** | プロンプト/完了トークン × モデル単価 | コスト管理 |
| **エラー** | 例外種別、スタックトレース | 障害分析 |
| **環境情報** | Python バージョン、OS、パッケージ | 再現性確保 |

### 2.3 ダッシュボード活用

AgentOps ダッシュボードで確認すべき主要指標:

| パネル | 確認内容 | アクション基準 |
|:---|:---|:---|
| **Total Duration** | セッション全体の実行時間 | SLO 超過時にアラート |
| **Token Usage** | プロンプト/完了トークンの内訳 | 予想外のトークン消費を検出 |
| **LLM Call Timing** | 各 LLM 呼び出しのレイテンシ | ボトルネックの特定 |
| **Estimated Cost** | セッション単位の推定コスト | 予算管理 |
| **Event Timeline** | エージェントのアクション時系列 | 異常行動の検出 |

---

## 3. LangSmith 統合ガイド

### 3.1 セットアップ

```bash
pip install langsmith
```

```python
# .env file
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY="your-api-key"
# LANGCHAIN_PROJECT="my-agent-project"

import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# Tracing is automatically enabled for LangChain components
```

### 3.2 主要機能

| 機能 | 説明 | 用途 |
|:---|:---|:---|
| **Tracing** | LLM 呼び出しチェーンの完全なトレース | デバッグ・パフォーマンス分析 |
| **Evaluation** | テストデータセットに対する自動評価 | 品質監視・回帰テスト |
| **Datasets** | テスト入力・期待出力の管理 | 評価パイプラインのデータ管理 |
| **Feedback** | ユーザーフィードバックの収集・分析 | 品質改善のインサイト |
| **Playground** | プロンプトの対話的テスト | プロンプトの反復改善 |

---

## 4. LangFuse 統合ガイド

### 4.1 セットアップ

```bash
pip install langfuse
```

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"  # or self-hosted URL
)
```

### 4.2 セルフホストオプション

| デプロイ方法 | 説明 | 適用場面 |
|:---|:---|:---|
| **Docker Compose** | 単一サーバーでの簡易デプロイ | 開発・テスト環境 |
| **Kubernetes** | スケーラブルなデプロイ | 本番環境 |
| **Cloud** | LangFuse Cloud（SaaS） | 管理負荷を最小化したい場合 |

### 4.3 主要機能

| 機能 | 説明 |
|:---|:---|
| **Traces** | リクエスト単位の完全なトレース |
| **Generations** | LLM 呼び出しの詳細（入出力、トークン、コスト） |
| **Scores** | カスタムスコアの記録（品質メトリクス） |
| **Datasets** | 評価用データセットの管理 |
| **Prompts** | プロンプトのバージョン管理 |

---

## 5. カスタム監視の実装パターン

### 5.1 構造化ログ設計

```python
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("agent-ops")

def log_agent_interaction(
    session_id: str,
    input_text: str,
    output_text: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    cost_usd: float,
    quality_scores: dict | None = None,
) -> None:
    """Log a structured agent interaction event."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "quality_scores": quality_scores,
    }
    logger.info(json.dumps(event, ensure_ascii=False))
```

### 5.2 メトリクス収集（Prometheus 形式）

| メトリクス名 | タイプ | ラベル | 説明 |
|:---|:---|:---|:---|
| `agent_requests_total` | Counter | model, status | リクエスト総数 |
| `agent_latency_seconds` | Histogram | model | レイテンシ分布 |
| `agent_tokens_total` | Counter | model, direction | トークン消費量 |
| `agent_cost_usd_total` | Counter | model | 累積コスト |
| `agent_errors_total` | Counter | model, error_type | エラー数 |
| `agent_quality_score` | Gauge | model, dimension | 品質スコア |
| `agent_guardrail_triggers_total` | Counter | layer, type | ガードレール発動数 |

### 5.3 アラートルール（Prometheus Alerting 形式）

```yaml
# Example: High error rate alert
- alert: AgentHighErrorRate
  expr: rate(agent_errors_total[5m]) / rate(agent_requests_total[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Agent error rate exceeds 5%"

# Example: Cost budget warning
- alert: AgentDailyCostWarning
  expr: sum(increase(agent_cost_usd_total[24h])) > (MONTHLY_BUDGET / 30 * 0.8)
  labels:
    severity: warning
  annotations:
    summary: "Daily cost approaching budget limit"

# Example: Latency degradation
- alert: AgentLatencyDegraded
  expr: histogram_quantile(0.95, rate(agent_latency_seconds_bucket[5m])) > 3
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "p95 latency exceeds 3 seconds"
```

---

## 6. ダッシュボード設計テンプレート

### 6.1 エグゼクティブダッシュボード

| パネル | 可視化 | データソース |
|:---|:---|:---|
| **Total Requests (24h)** | 数値（大きく表示） | `agent_requests_total` |
| **Success Rate (24h)** | ゲージ（緑/黄/赤） | 成功数 / 全数 |
| **Total Cost (MTD)** | 数値 + 予算比バー | `agent_cost_usd_total` |
| **Average Quality Score** | ゲージ（1-5） | `agent_quality_score` |
| **Request Trend** | 時系列グラフ（7日） | `rate(agent_requests_total)` |

### 6.2 運用ダッシュボード

| パネル | 可視化 | 用途 |
|:---|:---|:---|
| **Latency Distribution** | ヒートマップ | レイテンシのパターン分析 |
| **Token Usage by Model** | 積み上げ棒グラフ | モデル別コスト内訳 |
| **Error Breakdown** | 円グラフ / サンバースト | エラー種別の分布 |
| **Guardrail Triggers** | 時系列 + テーブル | セキュリティイベント追跡 |
| **Quality Score Trend** | 折れ線グラフ（6次元） | 品質の経時変化 |

### 6.3 デバッグダッシュボード

| パネル | 可視化 | 用途 |
|:---|:---|:---|
| **Recent Errors** | テーブル（時系列順） | 直近エラーの詳細確認 |
| **Slow Requests** | テーブル（レイテンシ順） | パフォーマンスボトルネック |
| **High Cost Sessions** | テーブル（コスト順） | コスト異常の調査 |
| **Guardrail False Positives** | テーブル + フィルター | 偽陽性の分析・チューニング |
| **Session Replay** | タイムライン | 特定セッションの再現 |

---

## 7. 監視のベストプラクティス

### 導入の優先順位

```
Phase 1: 基本ログ（構造化ログ + エラー追跡）
    ↓ 1 週間の運用データを蓄積
Phase 2: メトリクス（レイテンシ・コスト・エラー率）
    ↓ 閾値の初期設定
Phase 3: アラート（Critical / Warning の 2 段階）
    ↓ アラート精度の調整
Phase 4: ダッシュボード（運用→エグゼクティブ→デバッグ）
    ↓ チームへの展開
Phase 5: 評価統合（品質メトリクスの自動収集）
```

### アンチパターン

| アンチパターン | 問題 | 対策 |
|:---|:---|:---|
| **全てを記録** | ストレージコスト爆発、ノイズ過多 | サンプリング + 重要イベントのみ詳細記録 |
| **アラート過多** | アラート疲れ、重要なアラートの見逃し | Critical / Warning の 2 段階に絞る |
| **同期的なログ送信** | レイテンシ増加 | 非同期バッファリング |
| **監視なしの本番運用** | 障害検知の遅延、品質劣化の見逃し | 最低限の基本ログから開始 |
| **PII のログ記録** | コンプライアンス違反 | ログ前の PII マスキング |

### コスト管理

| 監視コスト要素 | 最適化方法 |
|:---|:---|
| **ストレージ** | ログの TTL 設定（30 日 hot / 90 日 cold） |
| **LLM 評価コスト** | サンプリング評価（10-20% に削減） |
| **ダッシュボードクエリ** | 事前集計テーブルの活用 |
| **アラート処理** | 重複排除 + グルーピング |
