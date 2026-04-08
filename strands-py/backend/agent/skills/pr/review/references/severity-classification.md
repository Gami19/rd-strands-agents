# レビュー指摘の重要度分類ガイド

> レビュー指摘に一貫した重要度を付与するための判断基準。Step 5 のレポート出力時に参照し、重要度のインフレを防止する。

---

## 重要度の 4 段階定義

| レベル | 定義 | 対応期限 | レポートでの扱い |
|:---|:---|:---|:---|
| **Critical** | データ損失・システム停止・セキュリティ侵害・目的達成を阻害する致命的な問題 | 即座に修正。リリースブロッカー | 必ず最上位に記載。修正案を具体的に提示 |
| **Warning** | ビジネスロジックの誤り・要件漏れ・パフォーマンス劣化など、運用に支障をきたす問題 | リリース前に修正必須 | 修正案を提示。条件付き承認の対象 |
| **Suggestion** | コード品質・可読性・保守性の改善余地。ベストプラクティスからの逸脱 | 次回イテレーションで対応可 | 改善案として記載。承認判定には影響しない |
| **Positive** | 優れた設計・実装・記述。他の箇所でも採用すべきパターン | — | レポート末尾に Good Points として記載 |

---

## 重要度判断マトリクス

重要度の判断に迷う場合、以下の 3 軸で評価する。

### 3 軸の定義

| 軸 | 説明 | 評価基準 |
|:---|:---|:---|
| **影響範囲** (Impact) | 問題が影響するユーザー数・データ量・機能範囲 | 全ユーザー / 特定ユーザー / 開発者のみ |
| **修正コスト** (Fix Cost) | 問題を修正するために必要な工数・複雑性 | 大規模リファクタ / 中規模修正 / 軽微な修正 |
| **発生確率** (Likelihood) | 問題が実際に顕在化する確率 | ほぼ確実 / 条件次第 / 稀 |

### 判断マトリクス

```
影響範囲: 大（全ユーザー・全データ）
  × 発生確率: 高（ほぼ確実）     → Critical
  × 発生確率: 中（条件次第）     → Critical / Warning
  × 発生確率: 低（稀）           → Warning

影響範囲: 中（特定ユーザー・特定機能）
  × 発生確率: 高（ほぼ確実）     → Warning
  × 発生確率: 中（条件次第）     → Warning
  × 発生確率: 低（稀）           → Suggestion

影響範囲: 小（開発者体験・保守性）
  × 発生確率: 高                 → Warning / Suggestion
  × 発生確率: 中                 → Suggestion
  × 発生確率: 低                 → Suggestion
```

### 修正コストによる調整

修正コストは重要度を直接決定しないが、対応の優先順位に影響する。

| 修正コスト | 調整ルール |
|:---|:---|
| **低**（数行の変更） | 重要度が Suggestion でも、即座に修正を推奨 |
| **中**（関数・クラス単位の変更） | 重要度に応じた標準的なスケジュールで対応 |
| **高**（アーキテクチャ変更） | Critical / Warning のみ対応必須。Suggestion は ADR に記録して先送り可 |

---

## 種別ごとの重要度判断ガイドライン

### コードレビューの重要度判断

| 問題の種類 | 典型的な重要度 | 判断のポイント |
|:---|:---|:---|
| SQL インジェクション | Critical | 攻撃ベクトルが存在する限り Critical。影響範囲に関わらず |
| 未処理の例外 | Warning → Critical | ユーザー向けエンドポイントなら Critical、内部バッチなら Warning |
| N+1 クエリ | Warning | データ量が少ない初期段階では Suggestion に下げてよい |
| 命名の不統一 | Suggestion | ただし、ドメインモデルの命名乖離は Warning |
| テスト未作成 | Warning | ビジネスクリティカルなロジックなら Critical に引き上げ |
| コメント不足 | Suggestion | 公開 API のドキュメント不足は Warning |

### ドキュメントレビューの重要度判断

| 問題の種類 | 典型的な重要度 | 判断のポイント |
|:---|:---|:---|
| 要件漏れ | Critical | RFP の配点項目であれば Critical。配点外なら Warning |
| 章間の数値矛盾 | Critical | 金額・工数の矛盾は Critical。表現の不統一は Suggestion |
| 積算根拠の不足 | Warning | 根拠がゼロなら Critical、根拠が弱いなら Warning |
| 誤字脱字 | Suggestion | ただし、固有名詞・顧客名の誤りは Warning |
| 図表の欠落 | Suggestion | 論理フローの理解に必須な図なら Warning |
| 用語の不統一 | Suggestion → Warning | 契約書・仕様書では Warning。社内ドキュメントなら Suggestion |

### アーキテクチャレビューの重要度判断

| 問題の種類 | 典型的な重要度 | 判断のポイント |
|:---|:---|:---|
| SPOF の存在 | Critical | 可用性要件が 99.9% 以上なら Critical。社内ツールなら Warning |
| RPO/RTO 未定義 | Critical | データ損失リスクがある本番系なら Critical |
| スケーリング未検討 | Warning | MVP / PoC フェーズなら Suggestion に下げてよい |
| コスト試算の欠如 | Warning | ランニングコストが月 10 万円以下なら Suggestion |
| オブザーバビリティ未設計 | Warning | 本番リリース前に必要だが、設計フェーズでは Suggestion |

### 提案書レビューの重要度判断

| 問題の種類 | 典型的な重要度 | 判断のポイント |
|:---|:---|:---|
| 課題定義の根拠不足 | Critical | 提案の出発点が揺らぐため、常に Critical |
| ROI の計算誤り | Critical | 投資判断に直結するため、常に Critical |
| 体制の過少見積もり | Warning → Critical | 工数の乖離が 30% 以上なら Critical |
| 競合比較の欠如 | Suggestion → Warning | コンペ案件では Warning、随意契約なら Suggestion |
| リスク対策の不足 | Warning | リスクの洗い出し自体がない場合は Critical |

---

## 重要度インフレ防止ガイドライン

レビューの信頼性を維持するため、重要度の過剰な引き上げ（インフレ）を防止する。

### インフレの兆候と対策

| # | インフレ兆候 | 検出方法 | 対策 |
|:---|:---|:---|:---|
| SI-1 | **全指摘が Critical** | Critical 率が 50% を超えている | マトリクスに立ち返り、影響範囲と発生確率を再評価する |
| SI-2 | **好みの強制** | 「自分ならこう書く」という理由で Warning にしている | レビュー基準（チェックリスト ID）に紐づかない指摘は Suggestion に下げる |
| SI-3 | **完璧主義の押し付け** | Suggestion 相当の品質改善を Warning で報告している | 「修正しなくても動作に支障がない」なら Suggestion |
| SI-4 | **重複指摘の積み上げ** | 同根の問題を複数の Critical として計上している | 根本原因を 1 つの指摘にまとめ、影響箇所をリストで列挙する |
| SI-5 | **文脈無視の機械的判定** | MVP の PoC コードに本番品質基準を適用している | レビューのスコープと目的を Step 1 で明確にする |

### 健全な重要度配分の目安

| 指標 | 健全な範囲 | 警告域 |
|:---|:---|:---|
| Critical 率 | 0-20% | 30% 超は要検証 |
| Warning 率 | 30-60% | 10% 未満は観点漏れの可能性 |
| Suggestion 率 | 20-50% | 5% 未満は表面的レビューの可能性 |
| Positive 率 | 5-15% | 0% はレビューの対立構造を助長 |

> **核心原則**: 重要度は「レビューアの不安の大きさ」ではなく、「ユーザーへの影響の大きさ」で決定する。

---

## 構造化出力との対応

SKILL.md の Structured Output Format（JSON Schema）における重要度フィールドとの対応。

### severity フィールドの値マッピング

| 本ガイドのレベル | JSON severity 値 | JSON findings での扱い |
|:---|:---|:---|
| Critical | `"critical"` | `findings[]` に含める。`resolved: false` が初期値 |
| Warning | `"major"` | `findings[]` に含める。`resolved: false` が初期値 |
| Suggestion | `"minor"` | `findings[]` に含める。承認判定には不算入 |
| Positive | `"suggestion"` | `findings[]` に含める。`severity: "suggestion"` で記録 |

> **注意**: SKILL.md の JSON Schema では `critical / major / minor / suggestion` の 4 値を使用する。本ガイドの `Critical = critical`、`Warning = major`、`Suggestion = minor`、`Positive = suggestion` に対応する。

### summary.overall_score との対応

| スコア | 判定条件 |
|:---|:---|
| **S** | Critical 0 + Warning 0 + Suggestion 2 以下 |
| **A** | Critical 0 + Warning 0 + Suggestion 3 以上 |
| **B** | Critical 0 + Warning 1-3 |
| **C** | Critical 0 + Warning 4 以上、または Critical 1-2 |
| **D** | Critical 3 以上 |

### category フィールドとの対応

指摘のカテゴリは SKILL.md のステップ番号に対応する。

| category 値 | 対応ステップ | 説明 |
|:---|:---|:---|
| `A-1` | Step 2 2a | 要件カバレッジ |
| `A-2` | Step 2 2b | 章間整合性 |
| `A-3` | Step 2 2c | 数値・データの妥当性 |
| `A-4` | Step 2 2d | 可読性と説得力 |
| `B-1` | Step 3 3a | Semantic Drift |
| `B-2` | Step 3 3b | Accounting Integrity |
| `B-3` | Step 3 3c | Edge Case Attack |
| `B-4` | Step 3 3d | Privacy Violation |
| `B-5` | Step 3 3e | Performance & Scalability |
| `B-6` | Step 3 3f | Test Coverage |

---

## 判断に迷うケースの FAQ

| ケース | 判断 | 根拠 |
|:---|:---|:---|
| セキュリティ問題だが、内部ネットワークからのみアクセス可能 | Warning | 影響範囲は限定的だが、将来の公開可能性を考慮 |
| テストが存在しないが、コード自体は正しく動作する | Warning | 退行リスクが高い。ビジネスクリティカルなら Critical |
| 命名規則の違反が 20 箇所以上ある | Warning（1 件） | 同根の問題は 1 指摘にまとめる（SI-4 防止） |
| 提案書の誤字が顧客名にある | Warning | 顧客への信頼に影響するため Suggestion ではなく Warning |
| アーキテクチャ図がない | Warning → Critical | 技術提案書なら Critical、運用手順書なら Warning |
| パフォーマンスが遅いが SLA 内 | Suggestion | SLA を満たしている限り Suggestion。ただし劣化傾向なら Warning |
| 廃止予定の API を使用している | Warning | 廃止時期が 6 ヶ月以内なら Critical に引き上げ |
| ログレベルが不適切（INFO で出すべきを DEBUG で出力） | Suggestion | 運用上の影響は軽微。ただし障害対応に支障があれば Warning |
