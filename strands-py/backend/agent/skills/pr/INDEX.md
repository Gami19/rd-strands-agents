# Skills Index -- KC-Vibe-kc-AIPR

> `.agents/skills/` に収録された 29 スキルのカテゴリマップ。
> マーケティング / 広報活動 + 開発加速に最適化されたスキルセット。

---

## カテゴリ俯瞰

```
marketing (5)     marketing-context, ad-creative, marketing-copy, seo-analytics, growth-ops
design (6)        distill, diagram, decision-framework, software-architecture, flow-architecture, story-map
develop (9)       front-design, ui-design, ux-psychology, effective-typescript, robust-python, agent-craft, ai-agents, comm-craft, project-ops
quality (6)       review, test, data-validation, agent-ops, incident-response, observability
capture (1)       pdf-convert
learning (1)      onboarding
forge (1)         skill-forge
```

---

## スキル連携図

```
                ┌────────────────────────────────────────────────────────────┐
                │               marketing-context (基盤)                    │
                └──────────┬──────────────────────┬──────────────────────────┘
                           │                      │
          ┌────────────────┴────────┐    ┌────────┴─────────────────────────┐
          │   マーケティング系       │    │   開発系                         │
          │                         │    │                                  │
          │  front-design           │    │  flow-architecture               │
          │  ux-psychology          │    │    └→ software-architecture      │
          │  ui-design              │    │         ├→ decision-framework    │
          │  seo-analytics          │    │         └→ story-map             │
          │  marketing-copy         │    │                                  │
          │  ad-creative            │    │  ai-agents                       │
          │  growth-ops             │    │    └→ agent-craft                │
          │                         │    │         └→ agent-ops             │
          └────────────┬────────────┘    │                                  │
                       │                 │  effective-typescript             │
                       │                 │  robust-python                   │
                       │                 │  comm-craft                      │
                       │                 │  project-ops                     │
                       │                 │    ├→ incident-response          │
                       │                 │    └→ observability              │
                       │                 └──────────────┬───────────────────┘
                       │                                │
                       └────────────┬───────────────────┘
                                    v
                          ┌──────────────────┐
                          │  品質ゲート       │
                          │  review + test   │
                          │  data-validation │
                          └──────────────────┘
```

---

## marketing -- マーケティング

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [marketing-context](marketing-context/SKILL.md) | v1.1.0 | ペルソナ・ブランドボイス・競合分析・KPI の基盤構築 | 「ペルソナを定義して」「ブランドボイスを決めて」 |
| [ad-creative](ad-creative/SKILL.md) | v1.1.0 | Google/Meta/LinkedIn Ads の広告クリエイティブ生成・最適化 | 「広告コピーを作って」 |
| [marketing-copy](marketing-copy/SKILL.md) | v1.1.0 | LP・メール・SNS・ブログのコピー執筆 | 「LP のコピーを書いて」「SNS 投稿を作って」 |
| [seo-analytics](seo-analytics/SKILL.md) | v1.1.0 | 技術 SEO 監査・AI 検索最適化・GA4/GTM 設計 | 「SEO 監査をして」 |
| [growth-ops](growth-ops/SKILL.md) | v1.1.0 | CRO・グロース実験・ファネル分析・リテンション | 「CVR を改善したい」「ファネルを分析して」 |

---

## design -- 上流設計

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [distill](distill/SKILL.md) | v1.6.0 | ソース資料 (inbox) -> 構造化仕様 (notes) への蒸留 | 「inbox を notes に蒸留して」 |
| [diagram](diagram/SKILL.md) | v1.3.0 | draw.io 図面の自動生成 | 「構成図を描いて」「フロー図を作って」 |
| [decision-framework](decision-framework/SKILL.md) | v1.1.0 | ADR 作成・トレードオフ分析・意思決定の構造化 | 「ADR を管理したい」 |
| [software-architecture](software-architecture/SKILL.md) | v1.0.0 | 9種アーキテクチャスタイル比較選定・特性分析・ADR生成 | 「アーキテクチャを設計して」「モノリスかマイクロサービスか」 |
| [flow-architecture](flow-architecture/SKILL.md) | v1.0.0 | Wardley Mapping × DDD × Team Topologies 統合設計 | 「フローアーキテクチャを設計して」「レガシーを近代化したい」 |
| [story-map](story-map/SKILL.md) | v1.2.0 | Jeff Patton 型ストーリーマッピング・MVP定義・リリース計画 | 「ストーリーマップを作成して」「MVP を定義して」 |

---

## develop -- 実装支援

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [front-design](front-design/SKILL.md) | v1.2.0 | LP・ウェブサイトのビジュアル戦略・カラー・タイポ・CSS | 「LP のデザインを準備して」 |
| [ui-design](ui-design/SKILL.md) | v1.2.0 | UI 設計・レイアウト・カラーパレット | 「UI を改善して」 |
| [ux-psychology](ux-psychology/SKILL.md) | v1.2.0 | UX 心理学に基づく設計評価・認知負荷分析 | 「UX 心理学でレビューして」 |
| [effective-typescript](effective-typescript/SKILL.md) | v1.0.0 | 『Effective TypeScript 第2版』(83項目) ベースのTS設計・レビュー | 「TS のコードをレビューして」「any を減らしたい」 |
| [robust-python](robust-python/SKILL.md) | v1.0.0 | 『ロバスト Python』(24章) ベースの型設計・クラス設計・拡張性改善 | 「Python のコードをレビューして」「型を設計して」 |
| [agent-craft](agent-craft/SKILL.md) | v1.1.0 | Claude Code カスタムエージェント設計・生成（5アーキタイプ） | 「カスタムエージェントを作って」 |
| [ai-agents](ai-agents/SKILL.md) | v1.0.0 | AIエージェントシステム設計（Five Pillars・マルチエージェント構成） | 「AI エージェントを設計して」「マルチエージェント構成を設計したい」 |
| [comm-craft](comm-craft/SKILL.md) | v1.0.0 | 技術コミュニケーション・交渉・リーダーシップ・プレゼン設計 | 「プレゼン資料の構成を考えて」「交渉戦略を立てて」 |
| [project-ops](project-ops/SKILL.md) | v1.0.0 | プロジェクト運用・認知負荷最適化・DORA改善・ボトルネック特定 | 「DORA メトリクスを改善したい」「ボトルネックを特定して」 |

---

## quality -- 品質保証

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [review](review/SKILL.md) | v1.7.0 | 成果物のクリティカルレビュー | 「レビューして」 |
| [test](test/SKILL.md) | v1.1.0 | テスト設計・生成 | 「テストを書いて」 |
| [data-validation](data-validation/SKILL.md) | v1.4.0 | データ品質・数値整合性の検証 | 「数値を検証して」 |
| [agent-ops](agent-ops/SKILL.md) | v1.0.0 | エージェント運用・評価・4層ガードレール・コスト最適化 | 「エージェントの品質を評価して」「ガードレールを設計して」 |
| [incident-response](incident-response/SKILL.md) | v1.0.0 | SRE/インシデント管理・SLO/エラーバジェット設計・ポストモーテム | 「インシデント対応フローを設計して」「SLO を設計して」 |
| [observability](observability/SKILL.md) | v1.0.0 | OpenTelemetry計装・SLOベースアラート・テレメトリパイプライン | 「オブザーバビリティを導入したい」「OpenTelemetry の計装を設計して」 |

---

## capture -- 情報取り込み

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [pdf-convert](pdf-convert/SKILL.md) | v1.3.0 | PDF/DOCX/PPTX を Markdown に変換 | 「PDF を変換して」 |

---

## learning -- 学習支援

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [onboarding](onboarding/SKILL.md) | v1.1.0 | 新人オンボーディング支援・学習ナビ・クイズ | 「次に何を学べばいい？」 |

---

## forge -- スキル開発

| スキル | バージョン | 概要 | トリガー例 |
|:---|:---:|:---|:---|
| [skill-forge](skill-forge/SKILL.md) | v1.3.0 | PDF/書籍 → 知識蒸留 → SKILL.md 鋳造のフルパイプライン | 「スキルを作って」「PDF からスキルを作って」 |

---

## 目的別スキル逆引き

| やりたいこと | 使うスキル |
|:---|:---|
| マーケティング基盤を構築したい | `marketing-context` |
| LP / メール / SNS のコピーを書きたい | `marketing-copy` |
| 広告クリエイティブを生成したい | `ad-creative` |
| SEO を強化したい | `seo-analytics` |
| CVR / リテンションを改善したい | `growth-ops` |
| 要件を構造化したい | `distill` |
| 構成図を作りたい | `diagram` |
| 意思決定を記録したい | `decision-framework` |
| アーキテクチャを設計したい | `software-architecture` |
| フロー最適化・レガシー近代化 | `flow-architecture` |
| ストーリーマップ・MVP定義 | `story-map` |
| LP のデザインを準備したい | `front-design` |
| UI を改善したい | `ui-design` |
| UX 心理学で評価したい | `ux-psychology` |
| TypeScript の設計・レビュー | `effective-typescript` |
| Python の型設計・ロバスト化 | `robust-python` |
| カスタムエージェントを作りたい | `agent-craft` |
| AIエージェントシステムを設計したい | `ai-agents` |
| プレゼン・交渉戦略を立てたい | `comm-craft` |
| DORA改善・ボトルネック特定 | `project-ops` |
| 成果物をレビューしたい | `review` |
| テストを書きたい | `test` |
| 数値の整合性を検証したい | `data-validation` |
| エージェント運用・評価 | `agent-ops` |
| インシデント対応・SLO設計 | `incident-response` |
| オブザーバビリティ導入 | `observability` |
| PDF を取り込みたい | `pdf-convert` |
| 新人の学習をサポートしたい | `onboarding` |
| 新しいスキルを鋳造したい | `skill-forge` |

---

## 開発ワークフロー

```
1. flow-architecture       -> 戦略×設計×チーム統合
2. software-architecture   -> アーキテクチャスタイル選定
3. story-map               -> ストーリーマッピング・MVP定義
4. decision-framework      -> ADR・トレードオフ分析
5. ai-agents               -> エージェントシステム設計
6. agent-craft             -> カスタムエージェント生成
7. effective-typescript     -> フロントエンド実装（Astro/TS）
8. robust-python           -> バックエンド実装（FastAPI/Python）
9. project-ops             -> フロー最適化・DORA改善
10. agent-ops + test + review -> 品質ゲート通過
11. observability           -> テレメトリ・監視設計
12. incident-response       -> SLO・インシデント対応
```

## マーケティングワークフロー

```
1. marketing-context -> 基盤構築（ペルソナ・ブランドボイス・KPI）
2. front-design      -> ビジュアル戦略・カラー・タイポ・CSS
3. seo-analytics     -> 技術 SEO 監査・GA4/GTM 設計
4. marketing-copy    -> LP/メール/SNS/ブログコピー
5. ad-creative       -> Google/Meta 広告クリエイティブ
6. growth-ops        -> ファネル分析・CRO・リテンション
7. review + data-validation -> 品質検証・数値検証
```

詳細: `.agents/workflows/marketing-workflow.md`
