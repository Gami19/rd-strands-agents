---
name: ai-agents
description: >
  AI エージェントシステムの設計・アーキテクチャ選定・コンポーネント構成を、
  書籍『AI Agents in Action』の Five Pillars フレームワークに基づいて支援する。
  自律性レベルの判定、マルチエージェント構成の設計、推論・計画・メモリ戦略の選定、
  ツール/アクション設計を包括的にガイドする。
  Use when user says「AIエージェントを設計して」「エージェントシステムのアーキテクチャを考えて」
  「マルチエージェント構成を設計したい」「エージェントに計画能力を持たせたい」
  「RAGをエージェントに組み込みたい」「エージェントの推論戦略を選びたい」
  「CrewAI/AutoGenの構成を考えて」「エージェントの自律性レベルを決めたい」。
  Do NOT use for: Claude Code カスタムエージェント(.claude/agents/)の作成（→ agent-craft。strands-py の YAML エージェントは dev の agent-craft-strands）、
  Agent Skill の作成（→ skill-forge）。
metadata:
  author: KC-Prop-Foundry
  version: 1.1.0
  category: development
  pattern: "domain-specific"
  based-on: "AI Agents in Action (Micheal Lanham, Manning 2025)"
---

# Skill: AI Agents（AI エージェントシステム設計）

> **エージェントは五本の柱で立つ — Profile・Actions・Knowledge・Reasoning・Planning の設計なくして、自律も協調もない**

## strands-py / Strands Agent での利用

設計書は **workspace 上の Markdown** を正とする。**pr の agent-craft / skill-forge は Strands ランタイムで除外**される。実装手順が必要なら **dev の agent-craft-strands** を参照。読み替えの詳細は [references/strands-py-runtime.md](references/strands-py-runtime.md)。

## Instructions

### ワークフロー内の位置

```
要件定義 → [ai-agents] → エージェント設計書
               ↓
          ・アーキテクチャパターン選定
          ・Five Pillars 設計
          ・推論/計画/メモリ戦略
          ・安全性/評価設計
               ↓
          agent-craft（Claude Code）/ agent-craft-strands（strands-py 実装）
          diagram（構成図出力）
          review（設計レビュー）
```

### 入力

| 入力 | 説明 | 例 |
|:---|:---|:---|
| エージェントの目的 | 何を達成するシステムか | 「顧客問い合わせの自動分類と回答」 |
| 対象ユーザー | 誰がシステムを使うか | 「サポートチーム」「エンドユーザー」 |
| 制約条件 | 技術・コスト・安全性の制約 | 「オンプレ限定」「GPT-4o のみ」 |
| 既存システム | 統合先や連携対象 | 「Slack + Jira + 社内 Wiki」 |

### 出力

| 出力 | 形式 | 説明 |
|:---|:---|:---|
| エージェント設計書 | Markdown | 全 7 ステップの設計結果を統合した設計文書 |
| アーキテクチャ選定理由書 | Markdown | パターン選定の根拠と比較評価 |
| コンポーネント構成表 | Markdown table | Five Pillars の各柱の設計仕様 |
| リスク・ガードレール定義 | Markdown | 安全性設計とフィードバック戦略 |

---

## Step 1: Goal & Scope Definition

エージェントシステムの目的と境界を明確にする。ここで曖昧さを残すと、後工程の全ての判断がブレる。

### 1a. 5W1H の確認

| 軸 | 質問 | 記録内容 |
|:---|:---|:---|
| **What** | 何を達成するシステムか？ | ゴールの定義 |
| **Who** | 誰が使い、誰がメンテするか？ | 対象ユーザーと運用チーム |
| **Where** | どの環境で動くか？ | クラウド/オンプレ/ハイブリッド |
| **When** | いつ・どの頻度で動くか？ | リアルタイム/バッチ/イベント駆動 |
| **Why** | なぜエージェントが必要か？ | 従来手法との差別化ポイント |
| **How** | どの LLM/フレームワークを使うか？ | 技術スタック候補 |

### 1b. 制約の洗い出し

| 制約カテゴリ | 確認項目 | 例 |
|:---|:---|:---|
| **技術** | LLM 選択制限、API 制限 | 「GPT-4o のみ」「レート制限 60rpm」 |
| **コスト** | トークン予算、インフラ予算 | 「月額 $500 以内」 |
| **安全性** | データ機密性、規制要件 | 「PII を LLM に送信不可」 |
| **パフォーマンス** | レスポンス時間要件 | 「3 秒以内に応答」 |
| **運用** | 監視、ログ、アラート要件 | 「AgentOps で全行動をログ」 |

**チェックリスト**:
- [ ] 5W1H の全軸を確認し、記録した
- [ ] 「なぜエージェントが必要か」の根拠が明確（単純な API 呼び出しで十分ではないか）
- [ ] 技術・コスト・安全性・パフォーマンス・運用の制約を洗い出した
- [ ] ステークホルダーの期待値を確認した

---

## Step 2: Autonomy Level Assessment

エージェントの自律性レベルを判定する。リスクと信頼の関数として、4 段階のレベルから選定する。

### 自律性レベル定義

| Level | Name | Description | User Role |
|:---|:---|:---|:---|
| **L0** | Direct Interaction | ユーザーが直接 LLM とやり取り | 全面的に制御 |
| **L1** | Proxy Agent | エージェントがリクエストを整形して LLM に渡す | 透明的仲介 |
| **L2** | Agent/Assistant | エージェントがツール実行前にユーザー承認を取得 | 承認ゲート |
| **L3** | Autonomous Agent | エージェントが計画・判断・実行を独立で行う | マイルストーン確認のみ |

### 判定フロー

```
エージェントが外部アクションを実行するか？
├─ No → L0（直接対話）or L1（プロキシ）
│    └─ プロンプトの整形・最適化が必要か？
│         ├─ Yes → L1: Proxy Agent
│         └─ No → L0: Direct Interaction
└─ Yes → アクション実行前にユーザー承認が必要か？
     ├─ Yes → L2: Agent/Assistant
     └─ No → L3: Autonomous Agent
          └─ ⚠ ガードレール設計が必須（Step 7 で詳細設計）
```

### レベル別リスクと対策

| Level | リスク | 必須対策 |
|:---|:---|:---|
| L0 | 低い | プロンプトインジェクション対策のみ |
| L1 | 低い | 入力バリデーション |
| L2 | 中程度 | 承認 UI、アクションログ、ロールバック機構 |
| L3 | 高い | ガードレール、評価ループ、kill switch、監視ダッシュボード |

**チェックリスト**:
- [ ] 4 つのレベルを検討し、最適なレベルを選定した
- [ ] 選定理由を根拠付きで記録した
- [ ] L3 を選定した場合、ガードレール設計の必要性を認識した
- [ ] ステークホルダーの信頼水準と一致しているか確認した

---

## Step 3: Architecture Pattern Selection

6 つのアーキテクチャパターンから、目的と制約に最適な構成を選定する。
詳細は [architecture-patterns.md](references/architecture-patterns.md) を参照。

### 6 パターン概要

| # | Pattern | Topology | Best For |
|:---|:---|:---|:---|
| A | **Single Agent** | 1 Agent + LLM | 単一ドメイン、単純なタスク |
| B | **Proxy Agent** | Proxy → Specialized Model | モデル間の仲介 |
| C | **Controller-Workers** | Controller + N Workers | マルチドメイン、並列処理 |
| D | **Group Chat** | N Agents (mesh) | ブレインストーミング、協調探索 |
| E | **Agentic Behavior Tree** | Root → Node Tree | 複雑なワークフロー、ロボティクス的制御 |
| F | **Platform Agent** | Full Stack (Nexus pattern) | 全 Five Pillars を統合 |

### 選定フロー

```
タスクは単一ドメインで完結するか？
├─ Yes → 単一エージェントで十分か？
│    ├─ Yes → Pattern A: Single Agent
│    └─ No（専門モデルが必要） → Pattern B: Proxy Agent
└─ No → 複数のエージェントが必要
     ├─ タスク構造は事前定義可能か？
     │    ├─ Yes → Pattern C: Controller-Workers
     │    │    or Pattern E: ABT（行動木制御が適切なら）
     │    └─ No → Pattern D: Group Chat
     └─ 全 Five Pillars の統合が必要か？
          └─ Yes → Pattern F: Platform Agent
```

### 通信パターンの選択

| Pattern | Communication | Control | Predictability |
|:---|:---|:---|:---|
| Proxy | Star topology | High | High |
| Group Chat | Mesh topology | Low | Variable |
| Hierarchical | Tree topology | High | High |
| Sequential (Pipeline) | Chain topology | High | High |
| Siloed (Parallel) | No inter-agent | Highest | Highest |

**チェックリスト**:
- [ ] 6 パターンを検討し、最適なパターンを選定した
- [ ] 選定理由を「なぜ他のパターンではないか」を含めて記録した
- [ ] 通信パターンを選定した
- [ ] パターンが Step 1 の制約条件と矛盾しないか確認した
- [ ] マルチエージェントの場合、各エージェントのロールを定義した

---

## Step 4: Five Pillars Design

選定したアーキテクチャの各柱を詳細設計する。
詳細は [five-pillars-guide.md](references/five-pillars-guide.md) を参照。

### Pillar 1: Profile & Persona

| 設計項目 | 内容 | 記録 |
|:---|:---|:---|
| **ロール定義** | エージェントの役割（1-2 文） | |
| **背景・専門性** | ドメイン知識の範囲 | |
| **トーン・スタイル** | 応答のスタイル | |
| **制約事項** | やらないこと | |
| **生成方法** | 手動 / LLM 支援 / データ駆動 | |

### Pillar 2: Actions & Tools

| 設計項目 | 内容 |
|:---|:---|
| **アクション一覧** | 各アクションの名前、入力、出力、副作用 |
| **Semantic vs. Native** | プロンプトベース vs. コードベースの分類 |
| **アクション数の適正化** | 1-3（低リスク）/ 4-7（要監視）/ 8+（要分割） |
| **安全性分類** | 読み取り専用 / 書き込み / 破壊的 の分類 |

### Pillar 3: Knowledge & Memory

Step 6 で詳細設計。ここではニーズの有無を判定。

| 質問 | Yes の場合 |
|:---|:---|
| 外部ドキュメントの参照が必要？ | → Knowledge (RAG) が必要 |
| 過去の対話履歴の参照が必要？ | → Memory が必要 |
| 長期的な学習が必要？ | → Persistent Memory が必要 |

### Pillar 4: Reasoning & Evaluation

Step 5 で詳細設計。ここでは推論の必要性を判定。

| 質問 | Yes の場合 |
|:---|:---|
| 多段階の思考プロセスが必要？ | → Chain of Thought |
| 複数の解法を比較したい？ | → Self-consistency / Tree of Thought |
| 出力品質の自己評価が必要？ | → Self-evaluation |

### Pillar 5: Planning & Feedback

Step 5 で詳細設計。ここでは計画の必要性を判定。

| 質問 | Yes の場合 |
|:---|:---|
| ツールを順序依存で使う？ | → Sequential Planning 必須 |
| 複数タスクを並列実行？ | → Parallel Planning |
| 途中で計画を変更する？ | → Feedback-enhanced Planning |

**チェックリスト**:
- [ ] Profile & Persona を定義した（ロール、専門性、トーン、制約）
- [ ] Actions & Tools を列挙し、Semantic/Native を分類した
- [ ] アクション数が適正範囲か確認した（8 以上なら分割を検討）
- [ ] Knowledge/Memory/Reasoning/Planning の必要性を判定した
- [ ] マルチエージェントの場合、全エージェントの Pillar 1-2 を定義した

---

## Step 5: Reasoning & Planning Strategy

推論技法と計画戦略を選定する。エージェントの「考える力」を設計する最重要ステップ。
詳細は [reasoning-techniques.md](references/reasoning-techniques.md) および [planning-strategies.md](references/planning-strategies.md) を参照。

### 5a. 推論技法の選定

| Technique | Complexity | Latency | Accuracy | Use When |
|:---|:---|:---|:---|:---|
| **Q&A** | Low | Fast | Moderate | 単純な事実質問 |
| **Few-shot** | Low | Fast | High (for known patterns) | 出力形式の指定 |
| **Zero-shot** | Low | Fast | Variable | 汎用タスク |
| **Chain of Thought** | Medium | Medium | High | 多段階推論 |
| **Zero-shot CoT** | Low | Medium | Moderate-High | 迅速な推論が必要 |
| **Prompt chaining** | Medium | Medium-High | High | 段階的分解 |
| **Self-consistency** | High | High | Very High | 精度最優先 |
| **Tree of Thought** | Highest | Highest | Highest | 複雑、多解法 |

### 推論技法の選定フロー

```
タスクは単純な事実質問か？
├─ Yes → Q&A or Few-shot
└─ No → ステップバイステップの思考が必要か？
     ├─ Yes → 精度が最優先か？
     │    ├─ Yes → Self-consistency or Tree of Thought
     │    └─ No → Chain of Thought or Zero-shot CoT
     └─ No → 問題を段階分解する必要があるか？
          ├─ Yes → Prompt chaining
          └─ No → Zero-shot
```

### 5b. 計画戦略の選定

| Strategy | Description | Use When |
|:---|:---|:---|
| **No Planner** | LLM のネイティブ対話 | ツール使用なし、or 全ツールが独立 |
| **Sequential** | ステップ順に実行 | ステップ間に依存関係あり |
| **Parallel** | 独立ステップを同時実行 | ステップが独立 |
| **Iterative** | 計画→実行→評価→再計画 | ゴールが曖昧、自律性が高い |
| **Feedback-enhanced** | Iterative + 外部フィードバック | 人間・環境からのフィードバックが利用可能 |

### 計画戦略の選定フロー

```
エージェントはツール/アクションを使うか？
├─ No → 計画不要（チャットボット）
└─ Yes → ツール間に依存関係があるか？
     ├─ No → Parallel Planning（多くの LLM がネイティブ対応）
     └─ Yes → ゴールは事前に明確か？
          ├─ Yes → Sequential Planning
          └─ No → フィードバック源があるか？
               ├─ Yes → Feedback-enhanced Planning
               └─ No → Iterative Planning（ガードレール必須）
```

**チェックリスト**:
- [ ] 推論技法を選定し、選定理由を記録した
- [ ] レイテンシ要件と精度要件のトレードオフを確認した
- [ ] 計画戦略を選定した
- [ ] Sequential Planning を選定した場合、LLM/プラットフォームがサポートしているか確認した
- [ ] Iterative Planning を選定した場合、終了条件と最大反復回数を定義した
- [ ] アプリケーション種別（個人/企業/研究）に応じた推論深度を決定した

---

## Step 6: Memory & Knowledge Architecture

RAG パイプライン、メモリタイプ、圧縮戦略を設計する。
詳細は [memory-design-guide.md](references/memory-design-guide.md) を参照。

### 6a. Knowledge (RAG) 設計

Step 4 で Knowledge が必要と判定された場合のみ。

| 設計項目 | 選択肢 | 記録 |
|:---|:---|:---|
| **ドキュメントソース** | PDF / Web / DB / API | |
| **チャンク戦略** | Character / Token / Recursive / Semantic | |
| **エンベディングモデル** | OpenAI / ローカル | |
| **ベクトル DB** | Chroma / Pinecone / Weaviate / pgvector | |
| **Top-K** | 検索結果の取得数 | |
| **再ランキング** | 類似度再計算の有無 | |

### 6b. Memory 設計

| Memory Type | Stores | Implementation |
|:---|:---|:---|
| **Semantic** | 事実、概念、関係 | Vector DB + fact tags |
| **Episodic** | 体験、イベント、対話履歴 | Vector DB + timestamp |
| **Procedural** | 手順、スキル、how-to | Vector DB + task tags |
| **Buffer** | 短期対話コンテキスト | In-memory list |
| **Summary** | 長期圧縮済みコンテキスト | Compressed summaries |

### 6c. 圧縮戦略

メモリエントリが 1000 件を超える場合、圧縮を検討する。

| 戦略 | 手法 | 効果 |
|:---|:---|:---|
| **Clustering** | 関連エントリをグループ化 | 冗長性の排除 |
| **Summarization** | 詳細エントリを要約に圧縮 | ストレージ削減 |
| **Hybrid** | Clustering + Summarization | 最大効果 |

**チェックリスト**:
- [ ] Knowledge (RAG) が必要な場合、パイプライン全体を設計した
- [ ] Memory が必要な場合、タイプ（Semantic/Episodic/Procedural）を選定した
- [ ] ベクトル DB を選定し、スケーラビリティを考慮した
- [ ] 圧縮戦略の必要性を判定した（予想エントリ数 > 1000 か）

---

## Step 7: Safety, Evaluation & Feedback

エージェントの安全性、品質評価、フィードバックループを設計する。L3（自律）エージェントでは最も重要なステップ。

### 7a. ガードレール設計

| ガードレール | 対象 Level | 実装方法 |
|:---|:---|:---|
| **入力バリデーション** | L0-L3 | プロンプトインジェクション対策、入力サニタイズ |
| **アクション承認ゲート** | L2 | 実行前にユーザー確認を要求 |
| **アクション制限リスト** | L2-L3 | 許可/禁止アクションの明示的定義 |
| **最大反復回数** | L3 | 無限ループ防止（推奨: 反復上限 10-20） |
| **Kill switch** | L3 | 強制停止メカニズム |
| **出力フィルタリング** | L0-L3 | 有害・不適切な出力の検出とブロック |
| **コスト上限** | L1-L3 | トークン使用量の上限設定 |

### 7b. 評価戦略

| 評価手法 | タイミング | 実装 |
|:---|:---|:---|
| **Rubric-based** | 設計時 | プロファイルの品質スコアリング |
| **Grounding** | 実行時 | 出力と参照データの一致度評価 |
| **Self-evaluation** | 実行時 | LLM による自己出力の評価 |
| **Cross-agent** | 実行時 | 別エージェントによる品質チェック |
| **Human feedback** | 事後 | ユーザーからの評価と修正 |
| **Batch comparison** | 設計時 | 複数プロファイル変種の比較評価 |

### 7c. フィードバックループ設計

| フィードバック源 | 説明 | 適用場面 |
|:---|:---|:---|
| **Environmental** | 実行結果からの自動フィードバック | API エラー、検索結果の品質 |
| **Human** | ユーザーからの明示的フィードバック | 承認、修正指示、評価 |
| **Self-generated** | エージェント自身の反省・評価 | 自律的改善ループ |

### 7d. モニタリング設計

| 監視項目 | ツール例 | 目的 |
|:---|:---|:---|
| **アクション履歴** | AgentOps, LangSmith | 行動のトレースと再現 |
| **トークン使用量** | Provider dashboard | コスト管理 |
| **応答品質** | 評価パイプライン | 品質の定量的追跡 |
| **エラー率** | 監視ダッシュボード | 障害の早期検出 |

### 7e. エージェント設計 Slop 防止チェック（Distributional Convergence 対策）

LLM によるエージェント設計は、ブログ記事やチュートリアルで頻出する「典型的なエージェント構成」に収束しやすい。ドメイン固有の制約・ユーザー特性・運用環境を反映しない「テンプレート設計」は、PoC では動くが本番で失敗するエージェントを生む。

| # | エージェント設計 Slop パターン | 検出方法 | 対策 |
|:---|:---|:---|:---|
| AA-1 | **ReAct ループ一辺倒** | すべてのエージェントが Thought→Action→Observation の同一ループ構造になっていないか確認 | タスク特性に応じて ReAct / Plan-then-Execute / Reflexion / LATS を使い分ける。単純タスクは ReAct 不要（直接関数呼び出しで十分）、複雑タスクは Plan-then-Execute が適切 |
| AA-2 | **Function Calling テンプレート直写し** | ツール定義が OpenAI の公式例（`get_weather`, `search_database`）と同構造か確認 | ドメイン固有の入出力スキーマを設計する。ツールの粒度（1アクション=1ツール vs 複合ツール）、エラーモデル、副作用の安全性分類を個別に定義 |
| AA-3 | **RAG 万能思考** | 外部知識が必要な場面でチャンク→エンベディング→ベクトル検索の RAG パイプラインを無条件に採用していないか確認 | 知識の特性に応じて RAG / Fine-tuning / Few-shot in-context / Tool-augmented retrieval / Knowledge Graph を比較検討する。構造化データなら SQL クエリ、小規模知識ならプロンプト内挿入が適切な場合もある |
| AA-4 | **階層型マルチエージェント一択** | マルチエージェント構成がすべて Controller→Worker の階層構造になっていないか確認 | 協調パターン（Mesh / Pipeline / Debate / Voting / Blackboard）をタスク特性に応じて選定する。独立タスクなら Siloed（並列独立）、探索的タスクなら Group Chat、厳密な順序ならPipeline |
| AA-5 | **入出力バリデーション画一化** | ガードレールがすべて「入力サニタイズ + 出力フィルタリング」の同一パターンか確認 | リスクプロファイルに応じたガードレール階層を設計する。L2 ならアクション承認ゲート、L3 ならコスト上限 + kill switch + 段階的権限昇格。ドメイン固有の安全性制約（PII、金融規制、医療情報）を反映 |
| AA-6 | **精度・コスト・レイテンシの3メトリクス固定** | 評価フレームワークがすべて同じ3指標（Accuracy / Cost / Latency）のみか確認 | ドメイン固有の評価指標を追加する。カスタマーサポートなら解決率・エスカレーション率、コード生成なら Pass@k・コンパイル成功率、リサーチなら網羅性・引用正確性 |
| AA-7 | **推論戦略の無条件適用** | タスク複雑度を評価せず CoT や ToT を一律適用していないか確認 | タスク複雑度（Cynefin フレームワーク: Clear/Complicated/Complex/Chaotic）に応じて推論深度を調整する。Clear タスクに CoT は過剰、Complex タスクに Zero-shot は不足 |
| AA-8 | **クラウドネイティブ構成の直写し** | デプロイアーキテクチャが「コンテナ + API Gateway + Vector DB + LLM API」の同一構成か確認 | 運用環境の制約（オンプレ/エッジ/ハイブリッド）、スケール要件（バッチ vs リアルタイム）、コスト構造（GPU 所有 vs API 従量課金）に応じた構成を設計する。小規模なら単一プロセス + SQLite で十分な場合もある |

> **核心原則**: **エージェントは生態系である** — 環境（ドメイン）に適応しない種は淘汰される。「別のドメインのエージェント設計にそのまま差し替えても違和感がないか？」→ 違和感がないなら Agent Design Slop である。

**チェックリスト**:
- [ ] 自律性レベルに応じたガードレールを設計した
- [ ] L3 の場合、kill switch と最大反復回数を定義した
- [ ] 評価戦略を 1 つ以上選定した
- [ ] フィードバックループの設計を完了した
- [ ] モニタリング体制を定義した（ツール、監視項目、アラート基準）
- [ ] 安全性設計書として文書化した
- [ ] エージェント設計 Slop チェック（AA-1〜AA-8）に 2 つ以上該当しない
- [ ] 出力がドメイン固有の要素を含み、汎用テンプレートに見えない

---

## Examples

### Example 1: カスタマーサポートボット（L2 + Single Agent + RAG）

```
「顧客からの問い合わせに FAQ から回答するエージェントを設計して」

→ Step 1: What=FAQ 回答、Who=サポートチーム、Where=クラウド、制約=PII 非送信
→ Step 2: L2（アクション実行前に承認が必要なケースあり）
→ Step 3: Pattern A（Single Agent）— 単一ドメイン、単純なタスク
→ Step 4: Profile=カスタマーサポート専門家、Actions=FAQ検索+チケット作成、
           Knowledge=RAG(社内FAQ)、Reasoning=Few-shot、Planning=不要
→ Step 5: Few-shot prompting（回答パターンの例示）、計画不要
→ Step 6: RAG: FAQ PDF → Token splitting → Chroma → Top-5
→ Step 7: 入力バリデーション + 出力フィルタリング + Human feedback
→ 成果物: エージェント設計書（Single Agent + RAG architecture）
```

### Example 2: コードレビューチーム（L2 + Controller-Workers + CoT）

```
「PR のコードレビューを自動化するマルチエージェントを設計して」

→ Step 1: What=コード品質チェック、Who=開発チーム、Where=CI/CD
→ Step 2: L2（修正提案は人間承認が必要）
→ Step 3: Pattern C（Controller-Workers）— Reviewer + Tester + Security Auditor
→ Step 4: Controller=PR分析→タスク分配、Worker各自にドメイン固有ルール
→ Step 5: CoT（各レビュアーがステップバイステップで分析）
→ Step 6: Knowledge=コーディング規約ドキュメント、Memory=過去レビュー履歴
→ Step 7: Cross-agent evaluation（各レビュアーが互いの指摘を検証）
→ 成果物: 3 エージェント構成のレビューシステム設計書
```

### Example 3: リサーチアシスタント（L3 + Iterative + ToT + RAG）

```
「学術論文を調査して研究動向レポートを自動生成するエージェントを設計して」

→ Step 1: What=論文調査+レポート生成、Where=サーバー、制約=arXiv+Semantic Scholar
→ Step 2: L3（自律的に論文収集→分析→レポート生成）
→ Step 3: Pattern A with Iterative Planning — 単一エージェント + 反復改善
→ Step 4: Actions=論文検索+PDF取得+要約生成+レポート作成
→ Step 5: Tree of Thought（複数の研究アングルを探索）、Iterative Planning
→ Step 6: RAG: 収集論文をリアルタイムインデックス、Episodic memory: 調査履歴
→ Step 7: Self-evaluation + 最大反復 5 回 + kill switch + コスト上限 $10/run
→ 成果物: 自律リサーチエージェント設計書
```

### Example 4: ソーシャルメディアパイプライン（L3 + ABT）

```
「YouTube 動画の要約を X に自動投稿するエージェントを設計して」

→ Step 1: What=動画要約→投稿、制約=YouTube API + X API
→ Step 2: L3（自律実行、マイルストーン通知のみ）
→ Step 3: Pattern E（ABT）— Sequence: 動画取得→要約→フォーマット→投稿
→ Step 4: Actions=YouTube API(動画取得)+LLM(要約)+X API(投稿)
→ Step 5: Prompt chaining（取得→要約→フォーマットの段階的処理）
→ Step 6: Memory=投稿済み動画リスト（重複防止）
→ Step 7: アクション制限（投稿は X のみ）+ 投稿前プレビュー（オプション）
→ 成果物: ABT ノード定義 + アクション仕様書
```

### Example 5: データ分析チーム（L2 + Group Chat + CrewAI）

```
「売上データを分析してインサイトレポートを作成するエージェントチームを設計して」

→ Step 1: What=売上分析、Who=経営層、Where=社内 BI 基盤
→ Step 2: L2（分析結果は人間が確認してから共有）
→ Step 3: Pattern D（Group Chat）— Analyst + Visualizer + Writer が協調
→ Step 4: Analyst=SQL実行+統計分析、Visualizer=グラフ生成、Writer=レポート執筆
→ Step 5: CoT（Analyst が分析ステップを明示）、Sequential Planning
→ Step 6: Knowledge=BI辞書+過去レポート、Memory=分析セッション履歴
→ Step 7: Cross-agent evaluation（Writer が Analyst の分析を検証）
→ 成果物: CrewAI 構成の 3 エージェントチーム設計書
```

### Example 6: BD 支援エージェント（L2 + Platform + Feedback）

```
「BD チームの提案書作成を支援するプラットフォーム型エージェントを設計して」

→ Step 1: What=提案書作成支援、Who=BD チーム、制約=CRM+社内テンプレート
→ Step 2: L2（提案書の最終版は人間が承認）
→ Step 3: Pattern F（Platform Agent）— 全 Five Pillars を統合
→ Step 4: Profile=BD コンサルタント、Actions=CRM検索+テンプレート適用+価格計算
           Knowledge=過去提案書+製品カタログ、Memory=案件履歴
→ Step 5: Few-shot + Sequential Planning（情報収集→分析→ドラフト→校正）
→ Step 6: RAG=製品カタログ+過去提案書、Semantic memory=顧客情報
→ Step 7: Human feedback（BD 担当のフィードバック）+ Rubric 評価
→ 成果物: フルスタック BD 支援エージェント設計書
```

---

## Troubleshooting

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| エージェントが計画なしにタスクを実行する | LLM がネイティブに Sequential Planning をサポートしていない | OpenAI Assistants / Claude に移行するか、カスタムプランナーを実装 |
| マルチエージェント間の通信がデッドロックする | 循環依存のある通信パターン | Controller-Workers パターンに切り替え、一方向の通信フローに変更 |
| RAG の検索結果が的外れ | チャンク粒度が粗すぎる / エンベディングモデルの品質 | チャンク戦略を Token splitting に変更、Top-K を増やして再ランキングを導入 |
| エージェントがツールを誤用する | ツール数が多すぎる / ツール説明が曖昧 | ツール数を 3-5 に絞る、各ツールの説明を具体的に書き直す |
| 自律エージェントが無限ループに陥る | 終了条件が未定義 / ゴールが曖昧 | maxTurns を設定（推奨 10-20）、明示的な終了条件をプロンプトに記載 |
| メモリが肥大化してパフォーマンス低下 | 圧縮戦略なし / 不要なメモリの蓄積 | Clustering + Summarization の圧縮を導入、TTL でメモリを自動削除 |
| 推論が深すぎてレスポンスが遅い | ToT / Self-consistency を不必要に使用 | アプリケーション種別に応じた推論深度を選定（リアルタイムなら CoT 以下） |
| フィードバックループが収束しない | 改善基準が曖昧 / 前回との差分が未追跡 | 定量的な品質スコアを導入、3 回連続で改善幅 < 閾値なら打ち切り |
| 自律性レベルの選択が不適切 | 信頼・リスクの評価不足 | Step 2 に戻り、ステークホルダーと合意の上で再判定 |
| エージェント間の責務分担が不明確 | ロール定義が曖昧 / 重複している | 各エージェントの Profile を独立して定義し、入出力の境界を明確化 |
| 計画の粒度が粗すぎる / 細かすぎる | タスク分解の基準が不明確 | 1 ステップ = 1 アクション呼び出しを基準に粒度を調整 |
| 評価メトリクスが出力品質を反映しない | 評価基準がドメインに合っていない | ドメイン固有の rubric を作成、Few-shot で評価基準の例を提供 |

---

## References

| ファイル | 内容 |
|:---|:---|
| [strands-py-runtime.md](references/strands-py-runtime.md) | strands-py（Strands Agent）での設計成果物の置き場・実装スキルの読み替え |
| [architecture-patterns.md](references/architecture-patterns.md) | 6 アーキテクチャパターンの詳細定義と選定ガイド |
| [five-pillars-guide.md](references/five-pillars-guide.md) | Five Pillars（Profile/Actions/Knowledge/Reasoning/Planning）の設計ガイド |
| [reasoning-techniques.md](references/reasoning-techniques.md) | 推論技法の比較・選定フロー・実装パターン |
| [planning-strategies.md](references/planning-strategies.md) | 計画戦略の比較・Application Matrix・フレームワーク別対応 |
| [memory-design-guide.md](references/memory-design-guide.md) | RAG パターン・メモリタイプ・圧縮戦略の設計ガイド |

## アンチパターン検出

このスキルの出力品質を検証するためのチェックリスト。

- [ ] Five Pillars（Profile/Actions/Knowledge/Reasoning/Planning）が全て設計されているか（欠落がないか）
- [ ] アーキテクチャ選定の根拠が具体的か（「マルチエージェントが良い」ではなく、なぜそのパターンか）
- [ ] 自律性レベルの選択がステークホルダーとのリスク合意に基づいているか
- [ ] 推論技法（CoT/ToT/Self-consistency）の選定がレスポンス時間要件と整合しているか
- [ ] エージェント間の責務分担が明確で、入出力の境界が定義されているか
- [ ] 評価基準がドメイン固有の rubric で定義されているか（汎用メトリクスのみで終わっていないか）

---

## Related Skills

| スキル | 関係 | 説明 |
|:---|:---|:---|
| **agent-craft** / **agent-craft-strands** | Downstream（実装） | Claude Code 実装は agent-craft。**strands-py** では pr の agent-craft は除外のため、YAML ベースの実装は **dev の agent-craft-strands** |
| **diagram** | 連携（構成図） | Step 3 のアーキテクチャ選定結果を draw.io 構成図として出力する場合に使用 |
| **review** | 品質検証 | 完成したエージェント設計書をレビューする場合に使用。Step 7 の評価戦略の外部実施 |
| **data-arch** | 姉妹（パターン類似） | 同じ Domain-specific + Sequential の複合パターン。データアーキテクチャ選定と同様の判断フレームワーク構造 |
| **test** | 連携（テスト設計） | エージェントの振る舞いテスト（発動テスト、ツール制限テスト、エッジケーステスト）を設計する場合に使用 |
| **robust-python** | 実装参考 | Python でエージェントシステムを実装する際のコーディングベストプラクティスを参照 |
