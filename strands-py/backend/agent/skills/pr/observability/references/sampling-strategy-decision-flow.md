# Sampling Strategy Decision Flow

> observability スキル補足資料 — サンプリング戦略の選択ガイドとデシジョンフロー

## 1. デシジョンフロー

```
┌────────────────────────────────────────┐
│ 秒間イベント数はいくつか？             │
└──────┬──────────┬──────────┬───────────┘
       ▼          ▼          ▼
  < 10K/sec   10K-100K/sec  > 100K/sec
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌───────────────┐
│ 全量保存  │ │ 中規模   │ │ 大規模戦略    │
│ or 固定率 │ │ 戦略     │ │               │
└──────┬───┘ └──────┬───┘ └──────┬────────┘
       │            │            │
       ▼            ▼            ▼
  サンプリング  キーベース    キー×履歴
  不要 or     動的サンプ    組合せ +
  50-100%     リング        ターゲットレート
       │            │            │
       ▼            ▼            ▼
┌──────────────────────────────────────────┐
│ エラー・外れ値を確実に捕捉する必要は？   │
└──────┬──────────────────────┬────────────┘
  Yes  ▼                      ▼ No
┌──────────────┐        ┌──────────────┐
│ Tail サンプ  │        │ Head サンプ  │
│ リング併用   │        │ リングのみ   │
└──────────────┘        └──────────────┘
```

---

## 2. サンプリング方式の比較

| 方式 | 判断タイミング | 判断基準 | 長所 | 短所 |
|:---|:---|:---|:---|:---|
| **固定率** | Head | 確率 | 実装が単純 | 希少イベント見逃し |
| **キーベース** | Head | フィールド値 | 重要キーの保証 | 動的判断不可 |
| **動的レート** | Head | トラフィック量 | コスト安定 | 履歴データ必要 |
| **Tail (status)** | Tail | status_code | エラー確実捕捉 | バッファリング必要 |
| **Tail (latency)** | Tail | duration_ms | 外れ値捕捉 | メモリ使用大 |
| **組合せ** | Head + Tail | 複合 | 最高精度 | 実装・運用複雑 |

---

## 3. Head サンプリング設計

### 固定率サンプリング

```yaml
# OTel SDK configuration
sampler:
  type: trace_id_ratio
  ratio: 0.1  # 10% of traces
```

**適用条件**: トラフィック均質、エラー率が一定、コスト制約が緩い

### キーベース動的サンプリング

高トラフィックのキーは低レートで、低トラフィックのキーは高レートでサンプリング。

```
Key: customer_id
  customer_A (10K req/sec) → sample rate: 1/100 (100 events/sec)
  customer_B (100 req/sec) → sample rate: 1/1   (100 events/sec)
  customer_C (1 req/sec)   → sample rate: 1/1   (1 event/sec)
```

**推奨キー**:
- `http.route` — エンドポイント別の均等分布
- `customer_id` — 顧客別の均等カバレッジ
- `status_code` — エラーの確実捕捉（4xx/5xx は 100%）

### ターゲットレートサンプリング

```yaml
# Target: 1000 events/sec regardless of traffic
target_rate:
  events_per_second: 1000
  adjustment_interval: 30s
  # Traffic 10K/sec → rate 1/10
  # Traffic 100K/sec → rate 1/100
  # Traffic 1K/sec → rate 1/1
```

---

## 4. Tail サンプリング設計

### OTel Collector Tail Sampling Processor

```yaml
processors:
  tail_sampling:
    decision_wait: 30s        # Wait for all spans to arrive
    num_traces: 100000         # Max traces in memory
    expected_new_traces_per_sec: 1000
    policies:
      # Rule 1: Always keep errors
      - name: keep-errors
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Rule 2: Always keep slow traces (> 1s)
      - name: keep-slow
        type: latency
        latency:
          threshold_ms: 1000

      # Rule 3: Always keep specific operations
      - name: keep-critical-ops
        type: string_attribute
        string_attribute:
          key: http.route
          values: ["/api/v1/payments", "/api/v1/auth"]

      # Rule 4: Sample normal traces at 5%
      - name: sample-normal
        type: probabilistic
        probabilistic:
          sampling_percentage: 5

      # Composite: combine policies
      # - name: composite-policy
      #   type: composite
      #   composite:
      #     max_total_spans_per_second: 5000
      #     policy_order: [keep-errors, keep-slow, keep-critical-ops, sample-normal]
```

### Tail サンプリングの注意事項

| 注意点 | 対策 |
|:---|:---|
| メモリ使用量 | `num_traces` を調整、`decision_wait` を短縮 |
| トレース不完全 | `decision_wait` を十分に取る（30-60s） |
| Gateway 必須 | Tail サンプリングは集約点でのみ有効 |
| スケーリング | トレース ID ベースのロードバランシングが必要 |

---

## 5. サンプルレートの記録と加重計算

### イベントにサンプルレートを埋め込む

```json
{
  "trace_id": "abc123",
  "service_name": "api-gateway",
  "duration_ms": 45,
  "sample_rate": 10,
  "status_code": 200
}
```

`sample_rate: 10` = このイベントは 10 件中 1 件を代表

### 加重集計の計算

```
■ COUNT (推定リクエスト総数)
  COUNT = Σ sample_rate_i
  例: 100 events × sample_rate 10 = 推定 1,000 requests

■ SUM (推定合計値)
  SUM = Σ (value_i × sample_rate_i)
  例: latency 45ms × rate 10 = 450ms 相当

■ PERCENTILE
  各イベントを sample_rate 分の重みで展開して計算
  ヒストグラムの各バケットに sample_rate を加算
```

---

## 6. コスト最適化ガイド

| トラフィック規模 | 推奨戦略 | 推定コスト削減 |
|:---|:---|:---|
| < 10K events/sec | 全量保存 | — |
| 10K-50K events/sec | Head キーベース (10%) | 90% |
| 50K-100K events/sec | Head + Tail 併用 (5%) | 95% |
| > 100K events/sec | ターゲットレート + Tail (1-3%) | 97-99% |

### コスト削減のベストプラクティス

1. **エラーは 100% 捕捉**: コスト削減でエラーを見逃すのは本末転倒
2. **段階的に導入**: 全量保存 → 50% → 10% と段階的に減らし、影響を確認
3. **ヘルスチェック/合成トラフィックを除外**: サンプリング前にフィルタリング
4. **低価値データを特定**: `/healthz`, `/metrics` 等は保存不要
5. **サンプルレートを必ず記録**: 加重計算で正確な集計を保証
