---
name: agent-craft
description: >
  Claude Code カスタムエージェント（.claude/agents/）の設計・生成を支援する。
  ユーザーの要件からエージェントのロール、ツール制限、モデル選択、システムプロンプトを
  構造化し、即座に使用可能な .md ファイルを出力する。
  Use when user says「カスタムエージェントを作って」「サブエージェントを作成して」
  「エージェントを追加して」「コードレビュー用のエージェントが欲しい」
  「専用のエージェントを設計して」「エージェントチームのメンバーを作って」
  「subagent を作成して」「agent を作って」
  「Five Pillars で設計して」「マルチエージェント構成を選びたい」
  「推論戦略を選定して」。
  Do NOT use for: Agent Skill の作成（→ skill-forge）、
  MCP サーバーの設定（→ MCP ドキュメント参照）。
metadata:
  author: KC-Prop-Foundry
  version: 1.2.0
  category: development
---

# Skill: Agent Craft（カスタムエージェントの設計・生成）

> **エージェントは「制約された専門家」— 何ができるかより何をさせないかを設計せよ**

## Instructions

### ワークフロー内の位置

```
要件ヒアリング → [agent-craft] → .claude/agents/<name>.md
                    ↓
               エージェント設計
               ・ロール定義
               ・ツール制限
               ・モデル選択
               ・システムプロンプト
```

### 入力

| 入力 | 説明 | 例 |
|:---|:---|:---|
| 目的・タスク | エージェントに実行させたい作業 | 「コードレビューを自動化したい」 |
| スコープ | 対象範囲と制約 | 「TypeScript のみ」「読み取り専用」 |
| チーム構成 | 単体 or チーム内の役割 | 「テストチームの一員」 |
| 既存エージェント | 参考にしたい既存定義 | `.claude/agents/reviewer.md` |

### 出力

| 出力 | 形式 | 説明 |
|:---|:---|:---|
| エージェント定義ファイル | `.md`（YAML frontmatter 付き） | `.claude/agents/` に配置可能なファイル |
| 設計根拠 | Markdown | アーキタイプ選定・ツール制限の理由 |
| テスト計画 | Markdown | 発動/非発動/制限のテストケース |

---

## Step 1: 要件ヒアリング

エージェントの目的とスコープを 5 軸で明確化する。

### 5 軸の確認

| 軸 | 質問 | 例 |
|:---|:---|:---|
| **目的** | 何を達成するエージェントか？ | コードの品質チェック |
| **スコープ** | 何に対して作用するか？ | TypeScript ファイルのみ |
| **対象ユーザー** | 誰が使うか？ | 開発チーム全員 |
| **チーム** | 単体 or チームの一員か？ | CI/CD パイプラインの一部 |
| **頻度** | どのくらいの頻度で使うか？ | PR ごとに実行 |

### 制約の特定

| 制約タイプ | 確認内容 |
|:---|:---|
| **読み取り/書き込み** | ファイル変更を許可するか？ |
| **Bash 実行** | コマンド実行を許可するか？許可する場合どの範囲？ |
| **外部通信** | WebFetch / WebSearch を許可するか？ |
| **コスト** | 高コストモデル（Opus）を使うか、低コスト（Haiku）で十分か？ |

**チェックリスト**:
- [ ] 5 軸（目的/スコープ/対象/チーム/頻度）を確認した
- [ ] 読み取り/書き込みの制約を決定した
- [ ] Bash 実行の可否と範囲を決定した
- [ ] 外部通信の可否を決定した
- [ ] コスト要件を確認した

---

## Step 2: エージェントタイプの決定

要件に基づき、5 つのアーキタイプから最適なタイプを選定する。

### 5 アーキタイプ

| アーキタイプ | 役割 | ツール傾向 | 典型的な用途 |
|:---|:---|:---|:---|
| **Inspector** | 読み取り分析 | Read / Grep / Glob のみ | コードレビュー、セキュリティ監査、ドキュメント分析 |
| **Worker** | 実装・変更 | 全ツール | コード生成、リファクタリング、テスト作成 |
| **Coordinator** | 調整・委譲 | Task + SendMessage | チームリーダー、ワークフロー管理 |
| **Specialist** | 特定ドメイン特化 | ドメイン依存 | DB 管理、インフラ構築、特定言語エキスパート |
| **Guardian** | 品質ゲート | Read + Bash（テスト実行） | CI ゲート、品質チェック、コンプライアンス |

### 選定基準

```
ファイルを変更するか？
  ├─ No → Inspector or Guardian
  │    └─ テスト/ビルドを実行するか？
  │         ├─ Yes → Guardian
  │         └─ No → Inspector
  │
  └─ Yes → Worker, Coordinator, or Specialist
       └─ 他のエージェントに委譲するか？
            ├─ Yes → Coordinator
            └─ No → 特定ドメインに限定か？
                 ├─ Yes → Specialist
                 └─ No → Worker
```

### アーキタイプ別テンプレート

詳細は [agent-patterns.md](references/agent-patterns.md) を参照。

### Five Pillars による設計軸（AI Agents in Action）

アーキタイプ選定後、Five Pillars（Profile / Actions / Knowledge / Reasoning / Planning）の各コンポーネントをどの程度組み込むかを決定する。

| Pillar | Inspector | Worker | Coordinator | Specialist | Guardian |
|:---|:---|:---|:---|:---|:---|
| **P1: Profile** | 分析観点を絞った厳格なペルソナ | 実装規約を埋め込んだ職人ペルソナ | リーダーシップスタイルを定義 | ドメイン専門家のペルソナ | 品質基準を体現する門番 |
| **P2: Actions** | Read/Grep/Glob（最小） | 全ツール or 拒否リスト | Task/SendMessage 中心 | ドメイン固有ツール | Read + Bash（テスト実行） |
| **P3: Knowledge** | `@ファイル参照`で規約注入 | `@ファイル参照`+ スキル連携 | チームメンバー情報 | RAG / 外部ナレッジベース連携 | 品質基準ドキュメント参照 |
| **P4: Reasoning** | Direct / CoT（分析レポート） | Direct（実装は推論より実行） | CoT（タスク分割判断） | CoT / Self-consistency | CoT（Pass/Fail 判定根拠） |
| **P5: Planning** | 不要（単発分析） | Sequential（実装→検証） | **必須** — タスク分割・委譲計画 | Sequential / Iterative | 不要（チェックリスト駆動） |

> **設計原則**: Planning を持つエージェントは chatbot ではなく真の agent になる（P5）。
> Inspector / Guardian は Planning 不要だが、Coordinator には必須。

**チェックリスト**:
- [ ] 5 アーキタイプから最適なタイプを選定した
- [ ] 選定根拠を明確にした
- [ ] 複合タイプの場合はベースタイプを決定した
- [ ] Five Pillars の各コンポーネントの採用レベルを決定した

---

## Step 3: ツールアクセスの設計

最小権限の原則に基づき、必要なツールのみを許可する。

### ツールカテゴリ

| カテゴリ | ツール | 用途 |
|:---|:---|:---|
| **ファイル読み取り** | Read, Glob, Grep | コード/ドキュメントの分析 |
| **ファイル書き込み** | Edit, Write, NotebookEdit | コード/ドキュメントの変更 |
| **実行** | Bash | コマンド実行、テスト、ビルド |
| **Web** | WebFetch, WebSearch | 外部情報の取得 |
| **チーム** | Task, SendMessage, TeamCreate | マルチエージェント連携 |
| **対話** | AskUserQuestion | ユーザーへの質問 |
| **スキル** | Skill | 既存スキルの発動 |

### ツール制限の書き方

```yaml
# 許可リスト方式（推奨 — Inspector / Guardian 向け）
allowedTools:
  - Read
  - Glob
  - Grep

# 拒否リスト方式（Worker / Specialist 向け）
disallowedTools:
  - WebFetch
  - WebSearch
  - TaskCreate
```

### 最小権限の設計パターン

| アーキタイプ | 推奨ツール構成 |
|:---|:---|
| **Inspector** | `allowedTools: [Read, Glob, Grep]` |
| **Worker** | `disallowedTools: [WebFetch, WebSearch]` （書き込み許可） |
| **Coordinator** | `allowedTools: [Read, Glob, Grep, Task, SendMessage, AskUserQuestion]` |
| **Specialist** | ドメインに必要なツールのみ許可 |
| **Guardian** | `allowedTools: [Read, Glob, Grep, Bash]` |

### Worktree 分離の判断基準

ファイル変更を伴う subagent は `isolation: worktree` を設定し、メインの作業ツリーとの衝突を防ぐ。

| 条件 | worktree 分離 | 理由 |
|:---|:---|:---|
| subagent がファイルを Edit/Write する | **必須** | メインエージェントとの競合を防止 |
| 複数 subagent が同じファイルを変更しうる | **必須** | マージコンフリクトの回避 |
| subagent が Read/Grep のみ（Inspector） | **不要** | 読み取り専用なら衝突しない |
| 長時間の分析タスク | **推奨** | メインのコンテキストを圧迫しない |

詳細は [tools-reference.md](references/tools-reference.md) を参照。

### マルチエージェント協調パターン

Coordinator アーキタイプを選定した場合、以下のパターンから協調方式を選定する。

| パターン | トポロジ | 特徴 | 適用場面 |
|:---|:---|:---|:---|
| **Sequential Pipeline** | Chain | エージェント間で順次処理を引き継ぐ | コード生成→テスト→レビューの段階的処理 |
| **Group Chat** | Mesh | 全エージェントが自由に対話 | ブレスト、探索的リサーチ、創造的タスク |
| **Hierarchical** | Tree | 階層的な指揮系統 | 大規模チーム、明確な責任分担 |
| **Behavior Trees (ABT)** | Tree (nodes) | Selector/Sequence ノードで条件分岐 | 自律的ワークフロー、フォールバック制御 |
| **Siloed** | Parallel | 独立実行→結果マージ | 独立サブタスクの並列処理 |

```
Coordinator パターン選定フロー:

サブタスク間に依存関係があるか？
├─ Yes → 順序が固定か？
│    ├─ Yes → Sequential Pipeline
│    └─ No → Hierarchical
└─ No → サブタスク数が多い（4+）か？
     ├─ Yes → Siloed（並列実行→マージ）
     └─ No → 創造性・探索が必要か？
          ├─ Yes → Group Chat
          └─ No → Sequential Pipeline
```

> **注意**: Group Chat は制御が難しく予測困難。構造化には Siloed、創発性には Group Chat を組み合わせるハイブリッドが実用的。

**チェックリスト**:
- [ ] 許可リスト方式 or 拒否リスト方式を決定した
- [ ] 最小権限の原則を満たしている
- [ ] 不要なツールが許可されていない
- [ ] 必要なツールが漏れていない
- [ ] ファイル変更を伴う subagent に worktree 分離を設定した
- [ ] Coordinator の場合、協調パターンを選定した

---

## Step 4: モデルと動作設定の決定

エージェントの実行パラメータを設定する。

### モデル選択

| モデル | 特徴 | 推奨用途 |
|:---|:---|:---|
| **claude-opus-4-6** | 最高性能。複雑な推論 | Coordinator、複雑な Specialist |
| **claude-sonnet-4-6** | バランス型。コスパ良好 | Worker、Guardian |
| **claude-haiku-4-5** | 高速・低コスト | Inspector、単純な繰り返しタスク |

### 動作設定

| パラメータ | 説明 | デフォルト | 設定例 |
|:---|:---|:---|:---|
| **model** | 使用モデル | 親エージェントと同じ | `claude-haiku-4-5` |
| **permissionMode** | 権限モード | `default` | `bypassPermissions` |
| **maxTurns** | 最大ターン数 | 制限なし | `10` |
| **background** | バックグラウンド実行 | `false` | `true` |
| **isolation** | ワークツリー分離 | なし | `worktree` |

### permissionMode の選択

| モード | 説明 | 推奨場面 |
|:---|:---|:---|
| `default` | 各ツール実行時にユーザー確認 | 初期テスト時 |
| `acceptEdits` | ファイル編集は自動承認 | Worker |
| `bypassPermissions` | 全ツール自動承認 | CI/CD パイプライン |
| `plan` | プラン承認が必要 | 影響範囲が大きい変更 |

**チェックリスト**:
- [ ] モデルをタスクの複雑さとコストに基づいて選定した
- [ ] permissionMode を安全性とユーザビリティのバランスで選定した
- [ ] maxTurns を設定した（無限ループ防止）
- [ ] background / isolation の要否を決定した

---

## Step 5: システムプロンプトの作成

エージェントの振る舞いを定義するプロンプトを作成する。

### 5a. 推論戦略の選定

システムプロンプトに組み込む推論方法を、タスク複雑度と正確性要求から選定する。

| 推論戦略 | 説明 | 正確性 | レイテンシ |
|:---|:---|:---|:---|
| **Direct / Few-shot** | 単発 Q&A、または入出力例で誘導 | 低-中 | 最小-小 |
| **CoT / Zero-shot CoT** | ステップバイステップ推論（例示あり/なし） | 中-高 | 中 |
| **Self-consistency** | 複数回生成→多数決で最良解を選定 | 最高 | 大 |
| **Tree-of-Thought (ToT)** | 複数パス探索→評価→最適解選定 | 最高 | 最大 |

```
単純で事実ベース？ → Yes → Direct / Few-shot
                  → No → ステップ思考が必要？ → Yes → 正確性最重要？ → Yes → Self-consistency / ToT
                                                                    → No  → CoT / Zero-shot CoT
                                              → No  → Direct / Zero-shot
```

> **組み込み方**: Instructions に「判断根拠を明示」（CoT）や「3通り検討し最善を選べ」（Self-consistency）等を追加。アーキタイプ別推奨は Step 2 Five Pillars テーブル P4 行を参照。

### プロンプト構成（推奨テンプレート）

```markdown
# <Agent Name>

## Role
<1-2文でエージェントの役割を定義>

## Scope
- 対象: <対象範囲>
- 除外: <対応しない範囲>

## Instructions
1. <手順1>
2. <手順2>
3. <手順3>

## Output Format
<出力の形式と構造>

## Constraints
- <制約1>
- <制約2>
```

### プロンプト設計の原則

| 原則 | 説明 |
|:---|:---|
| **簡潔性** | 500 語以内を推奨。長いプロンプトはコンテキストを圧迫する |
| **具体性** | 「良いコードを書け」ではなく「ESLint ルールに従い...」 |
| **出力形式の指定** | 何をどの形式で出力するかを明示 |
| **スコープの明示** | やること・やらないことを明確に |
| **例の提供** | 1-2 個の入出力例を含める（大きすぎない範囲で） |
| **自動委譲の促進** | プロンプトに「use subagents for heavy research」を含めると、エージェントが重い調査を subagent に自動委譲し、メインのコンテキストウィンドウを clean に保つ |

### コンテキストウィンドウの衛生管理

エージェント設計時に最も見落とされがちな品質要因。メインエージェントのコンテキストが溢れると、後半の推論品質が急激に低下する。

| 原則 | 説明 |
|:---|:---|
| **重い調査は subagent に委譲** | ファイル探索・コード検索など大量の結果を返す操作は subagent で実行し、要約だけメインに返す |
| **`@ファイル参照` の活用** | `@path/to/file` でコンテキストに必要なファイルを効率的に注入する |
| **中間結果のファイル保存** | 長い分析結果はファイルに書き出し、必要時に Read で参照する |
| **maxTurns でガードレール** | 長時間タスクでも maxTurns を設定し、中間報告を強制する |

### 避けるべきパターン

| パターン | 問題 | 改善 |
|:---|:---|:---|
| 「最善を尽くして」 | 曖昧すぎる | 具体的な基準を記述 |
| 1000 語以上のプロンプト | コンテキスト消費 | 核心だけに絞る |
| ツール使い方の説明 | 冗長（モデルは知っている） | ツール利用の制約のみ |
| 「エラーが起きたら...」の網羅 | 想定しすぎ | 主要なケースのみ |

### 5b. Agent Slop 防止チェック（Distributional Convergence 対策）

LLM がエージェント定義を生成する際にも distributional convergence が起きる。全エージェントが「同じプロンプト構造・同じ制約・同じ出力形式」に収束することを防ぐ。

| # | Agent Slop パターン | 検出サイン | 対策 |
|:---|:---|:---|:---|
| AS-1 | **Role が "helpful assistant" テンプレ** | 「〇〇の専門家として」「〇〇を支援する」の定型句で始まる | ドメイン固有の比喩で役割を定義する（例: 「TypeScript の型システムを盾として守る門番」「SQL クエリの外科医」） |
| AS-2 | **Constraints が汎用的** | 「ファイル変更不可」「破壊的コマンド禁止」等のアーキタイプデフォルトのみ | タスク固有の禁止事項を追加する（例: 「DELETE/DROP 文は WHERE 句なしで実行不可」「本番 DB への直接接続禁止」） |
| AS-3 | **Instructions が「分析→評価→報告」の3ステップ** | ドメインに関わらず同じフローになっている | ドメイン固有のワークフローを反映する（例: セキュリティ監査なら「OWASP Top 10 の各項目をスキャン→脆弱性の CVSS スコアを算出→修正優先度を判定」） |
| AS-4 | **Output Format が "構造化して報告"** | 出力の具体的な構造（セクション・フィールド・フォーマット）が定義されていない | 出力テンプレートを Markdown で明示する（ヘッダー、テーブル構造、必須フィールドを具体的に記述） |
| AS-5 | **Domain Knowledge が空** | Specialist タイプなのにドメイン固有の判断基準・ベストプラクティスがプロンプトに含まれない | 3-5 個のドメインルールを直接プロンプトに埋め込む（例: 「N+1 クエリは常に警告」「循環参照は Critical」） |
| AS-6 | **入出力例がない** | プロンプトに具体的な入出力例が1つもない | 最低 1 つの入出力例をプロンプトに含める。例は短くてよいが具体的であること |
| AS-7 | **ツール構成がアーキタイプデフォルトそのまま** | Inspector なら [Read, Glob, Grep]、Worker なら全ツール、のテンプレ通り | タスクに応じて微調整する（例: ログ分析 Inspector なら Bash も許可してログファイルの tail を実行可能にする） |
| AS-8 | **「人格」がない** | 同じアーキタイプの別エージェントと入れ替えても区別がつかない | エージェント固有の「スタンス」を1文で定義する（例: 「常に最悪のケースを想定して報告する悲観主義者」「パフォーマンスを1ms でも改善する執念の持ち主」） |

> **Why**: エージェントが均質化すると、チーム内の複数エージェントが同じ観点・同じ粒度で同じ結論を出す。
> 差別化されたエージェントだけが、チームとしての多角的な視点を提供できる。
>
> **核心原則**: **アーキタイプは骨格、ドメインは肉体、人格は魂** — テンプレートの構造に従いつつ、
> ドメイン固有の知識と個性的なスタンスで「このエージェントにしかできない仕事」を作る。

**チェックリスト**:
- [ ] 500 語以内に収まっている
- [ ] Role / Scope / Instructions / Output Format / Constraints が含まれている
- [ ] スコープ（やること/やらないこと）が明確
- [ ] 出力形式が具体的に指定されている
- [ ] 曖昧な指示がない
- [ ] Agent Slop チェック（AS-1〜AS-8）に 2 つ以上該当しない
- [ ] ドメイン固有の判断基準がプロンプトに含まれている

---

## Step 6: ファイル生成と配置

エージェント定義ファイルを生成し、適切な場所に配置する。

### 6a. ファイル形式

[agent-file-format.md](references/agent-file-format.md) を参照。

```yaml
---
name: <agent-name>
model: <model-id>
allowedTools:
  - <tool1>
  - <tool2>
modelConfig:
  maxTurns: <number>
---

<システムプロンプト（Markdown）>
```

### 6b. 配置場所

| 場所 | スコープ | 用途 |
|:---|:---|:---|
| `.claude/agents/<name>.md` | プロジェクト固有 | 特定リポジトリ専用のエージェント |
| `~/.claude/agents/<name>.md` | ユーザーグローバル | 全プロジェクトで使えるエージェント |

### 6c. ファイル命名規則

- kebab-case: `code-reviewer.md`
- 役割を端的に表す名前
- 接尾辞に `-agent` は不要（配置場所で明らか）

### 6d. ファイルの検証

- YAML frontmatter がパース可能であること
- 指定したツール名が正しいこと（[tools-reference.md](references/tools-reference.md) 参照）
- モデル ID が正しいこと

**チェックリスト**:
- [ ] YAML frontmatter が正しくパースできる
- [ ] ツール名が正しい（公式ツール名と一致）
- [ ] モデル ID が正しい
- [ ] 配置場所（プロジェクト / グローバル）を決定した
- [ ] ファイル名が kebab-case で役割を表している

---

## Step 7: 検証とテスト

生成したエージェントの動作を検証する。

### 7a. 発動テスト

| テスト | 方法 | 期待結果 |
|:---|:---|:---|
| **正常発動** | Task ツールで `subagent_type` に指定 | エージェントが起動する |
| **名前での呼び出し** | `/agent <name>` で呼び出し | エージェントが起動する |

### 7b. テストコマンドの実行

CLI から直接エージェントをテストする:

```bash
# JSON 出力でエージェントの応答を検証
claude -p "test agent: <name> with input: ..." --output-format json

# 特定エージェントの発動テスト
claude -p "Use the <name> agent to analyze this file" --output-format stream-json
```

### 7c. ツール制限テスト

| テスト | 方法 | 期待結果 |
|:---|:---|:---|
| **許可ツール** | 許可されたツールを使うタスクを依頼 | 正常に実行される |
| **制限ツール** | 制限されたツールを使うタスクを依頼 | ツールが使用されない |

### 7c. 出力品質テスト

| テスト | 確認項目 |
|:---|:---|
| **形式** | 指定した出力形式に従っているか |
| **スコープ** | 指定範囲外の作業をしていないか |
| **品質** | 出力の正確性と有用性 |

### 7d. エッジケーステスト

| テスト | 確認項目 |
|:---|:---|
| **大きなファイル** | パフォーマンスに問題がないか |
| **エラーケース** | 不正入力に対して適切にハンドリングするか |
| **maxTurns 到達** | ターン制限時に中間結果を報告するか |

### 7e. Agent Slop テスト

| テスト | 確認項目 |
|:---|:---|
| **差別化** | 同じアーキタイプの別エージェントと出力を比較して、ドメイン固有の差異があるか |
| **人格の一貫性** | 複数回の実行で「スタンス」が維持されているか |
| **ドメイン知識の発揮** | 汎用的な回答ではなく、ドメイン固有の知見に基づいた判断をしているか |

**チェックリスト**:
- [ ] 発動テストが成功した
- [ ] ツール制限が正しく機能している
- [ ] 出力形式が指定通りである
- [ ] スコープ外の作業をしていない
- [ ] エッジケースを確認した

---

## Examples

### Example 1: コードレビュー専用エージェント（Inspector）

```
「TypeScript のコードレビューを自動化するエージェントを作って」

→ Step 1: 目的=品質チェック、スコープ=TS ファイル、読み取り専用
→ Step 2: Inspector + Five Pillars: P1=型ハンター、P4=CoT（根拠明示）、P5=不要
→ Step 3: allowedTools = [Read, Glob, Grep]
→ Step 4: model = haiku, maxTurns = 10
→ Step 5: 推論=CoT、ESLint + Effective TypeScript 原則をプロンプトに
→ Step 6-7: .claude/agents/ts-reviewer.md に配置、テスト実行
```

### Example 2: テスト生成エージェント（Worker）

```
「既存コードに単体テストを追加するエージェントを作って」

→ Step 1: 目的=テスト生成、スコープ=全言語、書き込み必要
→ Step 2: Worker + Five Pillars: P1=AAA 職人、P4=Few-shot（例示駆動）、P5=Sequential
→ Step 3: disallowedTools = [WebFetch, WebSearch]
→ Step 4: model = sonnet, maxTurns = 20
→ Step 5: 推論=Few-shot、AAA パターンの入出力例をプロンプトに
→ Step 6: .claude/agents/test-writer.md に配置
```

### Example 3: マルチエージェントチームリーダー（Coordinator）

```
「フロントエンド開発チームのリーダーエージェントを作って」

→ Step 1: 目的=タスク分配、スコープ=フロントエンド、チーム管理
→ Step 2: Coordinator + Five Pillars: P1=QA長官、P4=CoT、P5=必須（タスク分割計画）
→ Step 3: allowedTools = [Read, Glob, Grep, Task, SendMessage, AskUserQuestion]
   協調パターン = Hierarchical（設計→実装→テストの階層委譲）
→ Step 4: model = opus, permissionMode = plan
→ Step 5: 推論=CoT、タスク分割基準とチームメンバー情報をプロンプトに
→ Step 6: .claude/agents/frontend-lead.md に配置
```

### Example 4: セキュリティ監査エージェント（Guardian）

```
「コミット前にセキュリティチェックを行うエージェントが欲しい」

→ Step 1: 目的=セキュリティ監査、スコープ=全コード、テスト実行
→ Step 2: Guardian + Five Pillars: P1=悲観主義の門番、P4=CoT（判定根拠）、P5=不要
→ Step 3: allowedTools = [Read, Glob, Grep, Bash]
→ Step 4: model = sonnet, maxTurns = 15
→ Step 5: 推論=CoT、OWASP Top 10 + Bandit ルールをプロンプトに
→ Step 6-7: .claude/agents/security-guard.md、破壊コマンド拒否を確認
```

---

## Troubleshooting

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| エージェントが起動しない | YAML 構文エラー / パス誤り | YAML frontmatter をバリデーション。パスを確認 |
| 制限したツールが使われる | ツール名のスペルミス | [tools-reference.md](references/tools-reference.md) で正式名を確認 |
| 出力品質が低い | プロンプトが曖昧 | 具体的な基準と出力形式をプロンプトに追加 |
| コストが高すぎる | Opus の不必要な使用 | Haiku / Sonnet に変更。maxTurns を制限 |
| 無限ループする | maxTurns 未設定 / 終了条件なし | maxTurns を設定。プロンプトに終了条件を明記 |
| チーム連携できない | 連携ツールが制限されている | Coordinator には Task / SendMessage を許可 |
| 生成エージェントが無個性 | Agent Slop（distributional convergence） | AS-1〜AS-8 を確認。Role の比喩・ドメイン Constraints・人格スタンスを検証 |
| 複数エージェントが同じ結論 | チーム内の差別化不足 | 各エージェントの「スタンス」を対立軸で設計（楽観/悲観、速度/品質） |
| プロンプトが 500 語超過 | ドメイン知識の詰め込みすぎ | 核心ルール 3-5 個に絞り、詳細は参照ファイルに分離 |
| subagent が期待と違う結果 | スコープと出力形式が曖昧 | Output Format を具体的に指定し、入出力例を 1 つ以上含める |

---

## References

| ファイル | 内容 |
|:---|:---|
| [agent-file-format.md](references/agent-file-format.md) | .claude/agents/ ファイル形式のリファレンス |
| [agent-patterns.md](references/agent-patterns.md) | 5 アーキタイプのテンプレート集 |
| [tools-reference.md](references/tools-reference.md) | ツールカタログと制限パターン |

---

## Related Skills

| スキル | 関係 | 説明 |
|:---|:---|:---|
| **skill-forge** | 姉妹スキル | Agent Skill を作る場合はこちら（エージェントではなくスキル） |
| **review** | 連携 | 生成したエージェントの品質レビュー |
| **effective-typescript** | 参考 | TypeScript 関連エージェントのプロンプト素材 |
| **robust-python** | 参考 | Python 関連エージェントのプロンプト素材 |
| **ai-agents** | Upstream（設計） | ai-agents がエージェントシステムの Five Pillars 設計を担当し、agent-craft が Claude Code での具体的な実装を担当。ai-agents Step 3-4 の設計結果を agent-craft で実現 |
| **agent-ops** | Downstream（運用） | agent-craft で実装したエージェントの運用・評価・ガードレール設計・コスト最適化を agent-ops が担当 |
| **flow-architecture** | 参考（社会技術設計） | Architecture for Flow の原則を適用してエージェントの社会技術的設計に応用可能 |
