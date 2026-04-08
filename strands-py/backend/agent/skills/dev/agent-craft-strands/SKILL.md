---
name: agent-craft-strands
description: >
  strands-py（Strands + FastAPI）向けのエージェント定義 YAML を設計し、
  project workspace の agents/ に保存する手順を支援する。
  Claude Code の .claude/agents/*.md ではない。
  Use when: Strands 用エージェント YAML、agents フォルダ、
  skills モード用の単体エージェント、orchestrate 用オーケストレータ定義、
  agent_id で選べる定義を作りたい、など。
  Do NOT use for: Claude Code 専用の .md エージェント、
  Agent Skill そのものの作成、Strands で未提供のツールや実行能力を前提にした設計。
metadata:
  author: KC-Prop-Foundry / strands-py
  version: 1.1.0
  category: development
---

# Skill: Agent Craft Strands（strands-py 用エージェント YAML）

> **エージェントは「制約された専門家」— 何ができるかより、何だけをさせるかを設計する。**  
> 本スキルは **Strands 専用**。Claude Code のツール名・権限モデル・発動方式は前提にしない。

## ワークフロー内の位置

```
要件ヒアリング → [agent-craft-strands] → agents/<agent_id>.yaml
                      ↓
                 エージェント設計
                 ・役割定義
                 ・ツール制限
                 ・kind 決定
                 ・system_prompt 設計
```

詳細なフィールド制約は [references/strands-yaml-schema.md](references/strands-yaml-schema.md) を参照。

---

## Strands 専用前提

- 出力先は `DATA_ROOT/projects/<project_id>/agents/<agent_id>.yaml`
- 本スキルが作るのは **Strands 用 YAML**
- Claude Code 用 `.claude/agents/*.md` は対象外
- Claude Code 固有ツールや設定値は使わない
- Strands で利用可能な能力だけで設計する
- 利用可能ツールで実現できない要件は、無理に埋めず制約として明示する

### 利用可能なツール名（allowed_tools）

次の **み**からサブセットを選ぶ。**`file_read` は必須**。

- `file_read`
- `file_write`
- `pdf_convert_to_inbox`
- `diagram_generate_drawio`
- `web_fetch_text`
- `brave_web_search`

> 重要: `allowed_tools` は **生成されるエージェント自身**が使えるツール。  
> 本スキルが保存時に使う `file_write` とは別である。

---

## 出力先と命名

- パス: `DATA_ROOT/projects/<project_id>/agents/<agent_id>.yaml`
- `project_id` は UI のプロジェクト。通常は `default` から始める
- ファイル名 stem と YAML 内 `id` は一致させる
- `id` は運用上 **必須**
- 識別子は `^[a-zA-Z0-9._-]+$` に合わせる
- 推奨は英小文字の kebab-case

---

## 入力

| 入力 | 説明 | 例 |
|:---|:---|:---|
| 目的・タスク | エージェントに実行させたい作業 | 「TypeScript のレビューをさせたい」 |
| スコープ | 対象範囲と制約 | 「読み取り専用」「Web 禁止」 |
| 生成物 | 期待する出力形式 | 「箇条書きレポート」「修正文案」 |
| 構成 | 単体 or 振り分け | `single` / `orchestrator` |
| 参考定義 | 既存 agent や期待動作 | `agents/reviewer.yaml` |

## 出力

| 出力 | 形式 | 説明 |
|:---|:---|:---|
| エージェント定義ファイル | `.yaml` | `agents/` に配置可能な Strands 用定義 |
| 設計根拠 | Markdown | kind・ツール制限・prompt 構成の理由 |
| 検証観点 | Markdown | ツール制約、出力形式、委譲の確認項目 |

---

## Step 1: 要件ヒアリング

エージェントの目的とスコープを 5 軸で明確化する。

### 5 軸の確認

| 軸 | 質問 | 例 |
|:---|:---|:---|
| **目的** | 何を達成するエージェントか？ | コードレビュー、PDF 要約 |
| **スコープ** | 何に対して作用するか？ | workspace 内ファイル、外部記事 |
| **成果物** | どんな出力を返すか？ | 箇条書き、表、修正案 |
| **構成** | 単体か、委譲前提か？ | `single` / `orchestrator` |
| **安全性** | 書き込み・Web・検索を許可するか？ | 読み取り専用、検索可 |

### 制約の特定

| 制約タイプ | 確認内容 |
|:---|:---|
| **読み取り/書き込み** | `file_write` を許可するか？ |
| **外部取得** | `web_fetch_text` を許可するか？ |
| **Web 検索** | `brave_web_search` を許可するか？ |
| **PDF** | `pdf_convert_to_inbox` が必要か？ |
| **図生成** | `diagram_generate_drawio` が必要か？ |
| **実現可能性** | Strands の利用可能ツールだけで要件を満たせるか？ |

**チェックリスト**:
- [ ] 5 軸（目的/スコープ/成果物/構成/安全性）を確認した
- [ ] 読み取り/書き込み制約を決定した
- [ ] 外部取得・検索の可否を決定した
- [ ] PDF / 図生成の要否を決定した
- [ ] Strands の利用可能ツールで実現可能か確認した

> **不可能要件の扱い**:  
> Strands に存在しない能力が中核要件なら、表現不能と明示し、要件を縮約または分割する。

---

## Step 2: エージェントタイプの決定

要件に基づき、Strands 向けの 5 アーキタイプから最適なタイプを選定する。

### 5 アーキタイプ

| アーキタイプ | 役割 | ツール傾向 | 典型的な用途 |
|:---|:---|:---|:---|
| **Reader** | 読み取り分析 | `file_read` のみ | コードレビュー、文書分析 |
| **Writer** | 更新・整形 | `file_read`, `file_write` | ドキュメント修正、定型更新 |
| **Researcher** | 外部情報収集 | `file_read` + Web/PDF | 調査、要約、比較 |
| **Synthesizer** | 複数ソース統合 | `file_read` + 必要最小限 | 要件整理、比較表、集約 |
| **Router** | 調整・委譲 | `file_read` + 必要最小限 | 振り分け、担当分離 |

### 選定基準

```text
ファイル変更を行うか？
  ├─ No → 外部情報や PDF を使うか？
  │    ├─ Yes → Researcher or Synthesizer
  │    └─ No → Reader or Synthesizer
  │
  └─ Yes → Writer

さらに複数の専門役割へ振り分けるか？
  ├─ Yes → Router（kind=orchestrator）
  └─ No → kind=single
```

### Strands 設計軸（簡易 Five Pillars）

アーキタイプ選定後、以下 5 軸をどの程度組み込むか決める。

| Pillar | Reader | Writer | Researcher | Synthesizer | Router |
|:---|:---|:---|:---|:---|:---|
| **P1: Profile** | 厳格な読み手 | 変更を最小化する編集者 | 出典重視の調査員 | 論点整理者 | 委譲に徹する指揮役 |
| **P2: Actions** | `file_read` 最小 | 読み書きのみ | Web/PDF を必要最小限 | 読み取り中心 | specialists への委譲中心 |
| **P3: Knowledge** | ルール・規約 | 更新対象の書式規約 | 出典評価基準 | 比較軸・整理軸 | 振り分け基準 |
| **P4: Reasoning** | 根拠付き評価 | 差分最小判断 | 情報の信頼性評価 | 統合と圧縮 | 委譲判断 |
| **P5: Planning** | 通常不要 | 軽い逐次手順 | 調査手順あり | 統合手順あり | **必須** |

> **原則**: Router は Planning を持つ。Reader は過剰計画を持たない。

**チェックリスト**:
- [ ] 5 アーキタイプから最適なタイプを選定した
- [ ] 選定根拠を明確にした
- [ ] `single` / `orchestrator` を決定した
- [ ] 5 つの設計軸の採用レベルを決定した

---

## Step 3: ツールアクセスの設計

最小権限の原則に基づき、必要なツールのみを許可する。

### 基本ルール

- `file_read` は必須
- 読み取り専用なら `file_write` を入れない
- Web を使わないなら `web_fetch_text` / `brave_web_search` を入れない
- PDF を扱わないなら `pdf_convert_to_inbox` を入れない
- 図を作らないなら `diagram_generate_drawio` を入れない
- 将来のための「予備ツール」は追加しない

### 推奨パターン

| アーキタイプ | 推奨 allowed_tools |
|:---|:---|
| **Reader** | `file_read` |
| **Writer** | `file_read`, `file_write` |
| **Researcher** | `file_read`, `web_fetch_text`（必要に応じて `brave_web_search`, `pdf_convert_to_inbox`） |
| **Synthesizer** | `file_read` + 必要最小限 |
| **Router** | `file_read`（必要時のみ `file_write`） |

### 注意事項

- Claude Code のツール名はそのまま使えない
- Strands で使えない能力を prompt だけで仮定しない
- whitelist にない能力が必要なら、要件を再設計する

**チェックリスト**:
- [ ] `file_read` を含めた
- [ ] 不要なツールが許可されていない
- [ ] 必要なツールが漏れていない
- [ ] Strands で実際に使えるツールだけを列挙した

---

## Step 4: kind の選択

| kind | 用途 |
|------|------|
| `single` | 1 体の専門エージェントとして動かす |
| `orchestrator` | specialists に振り分けるルータ/指揮役として動かす |
| `swarm` | YAML からの組み立て経路が未整備なことがあるため、主対象は `single` / `orchestrator` |

> **原則**: まずは `single` を優先し、明確な委譲要件がある場合のみ `orchestrator` を使う。

---

## Step 5: system_prompt の作成

`system_prompt` は振る舞いの核心。短くてもよいが、以下を含める。

### 推奨構成

```text
あなたは <役割> です。

対象:
- <扱う対象>
- <扱わない対象>

進め方:
1. ...
2. ...
3. ...

出力形式:
- <形式>
- <必須セクション>

制約:
- 許可されたツールのみを使う
- <禁止事項>
- 不足情報があれば、その不足を明示する

判断基準:
- <ドメインルール1>
- <ドメインルール2>
- <ドメインルール3>
```

### プロンプト設計の原則

| 原則 | 説明 |
|:---|:---|
| **簡潔性** | 長すぎる説明より、実行方針と制約を優先する |
| **具体性** | 対象・禁止事項・出力形式を明示する |
| **最小権限整合** | 許可ツールと prompt の能力仮定を一致させる |
| **出力形式の指定** | 何をどの順番で返すかを明示する |
| **ドメイン基準** | 汎用指示ではなく判断基準を入れる |
| **委譲明示** | Router は「自分で抱え込まず委譲」を書く |

---

## Step 6: Agent Slop 防止チェック

LLM が作る agent 定義は均質化しやすい。以下を避ける。

| # | Agent Slop パターン | 検出サイン | 対策 |
|:---|:---|:---|:---|
| AS-1 | **Role が汎用的** | 「有能なアシスタントです」で始まる | ドメイン固有の役割にする |
| AS-2 | **Constraints が弱い** | 禁止事項がほぼない | 対応しない範囲を明記する |
| AS-3 | **Instructions が凡庸** | 毎回「読む→分析→報告」だけ | ドメイン固有の進め方を入れる |
| AS-4 | **Output が曖昧** | 「わかりやすく報告」だけ | セクションや箇条書きを指定する |
| AS-5 | **Domain Knowledge が空** | どの agent でも同じ判断 | 固有ルールを 2〜5 個入れる |
| AS-6 | **差別化がない** | 別 agent と入れ替えても同じ | 固有スタンスを 1 文入れる |
| AS-7 | **ツール構成が惰性** | 必要ない Web や Write が入る | 要件に合わせて削る |
| AS-8 | **Strands 非対応能力を仮定** | 実在しない操作を指示 | 利用可能ツールだけで再設計する |

> **核心原則**: アーキタイプは骨格、ドメインは肉体、スタンスは魂。  
> YAML が正しいだけでは足りない。役割の差別化が必要。

**チェックリスト**:
- [ ] Role が具体的
- [ ] 制約が明確
- [ ] 出力形式が具体的
- [ ] ドメイン固有ルールがある
- [ ] 同系統 agent と区別できる
- [ ] Strands で使えない能力を仮定していない

---

## Step 7: YAML の組み立て

### 7a. single

```yaml
id: <agent_id>
name: <表示名>
kind: single
description: <短い説明>
system_prompt: |
  <system_prompt>
allowed_tools:
  - file_read
  # 必要に応じて追加
```

### 7b. orchestrator

```yaml
id: <agent_id>
name: <表示名>
kind: orchestrator
description: <短い説明>
system_prompt: |
  <委譲基準を中心にした system_prompt>
allowed_tools:
  - file_read
  # 必要に応じて追加
specialists:
  - tool_name: consult_<name1>
    name: <specialist-name1>
    role_instructions: <委譲先1の役割>
  - tool_name: consult_<name2>
    name: <specialist-name2>
    role_instructions: <委譲先2の役割>
```

### orchestrator の注意

- `specialists` は委譲先の意味が明確であること
- `tool_name` は Python 識別子規則 `^[a-z_][a-z0-9_]*$` に従う
- `tool_name` は重複不可
- orchestrator 自身は全部を自分で処理しない
- 委譲基準を `system_prompt` に書く

---

## Step 8: 保存と配置

- `file_write` で `agents/<agent_id>.yaml` に保存する
- project 外へ書かない
- `id` とファイル名 stem を一致させる

---

## Step 9: 検証とテスト

生成したエージェントの動作を最低限検証する。

### 9a. 構文・配置

- [ ] YAML が正しくパースできる
- [ ] `agents/<agent_id>.yaml` に保存されている
- [ ] `id` とファイル名が一致している
- [ ] schema 制約に適合している

### 9b. ツール制限テスト

| テスト | 方法 | 期待結果 |
|:---|:---|:---|
| **許可ツール** | 許可された操作を含む依頼をする | 正常に実行される |
| **制限ツール** | 未許可操作を含む依頼をする | 実行せず制約を説明する |

### 9c. 出力品質テスト

| テスト | 確認項目 |
|:---|:---|
| **形式** | 指定した出力形式に従うか |
| **スコープ** | 対象外の作業をしていないか |
| **根拠** | 判断に根拠や基準があるか |
| **差別化** | 他 agent と区別できる視点があるか |

### 9d. orchestrator テスト

| テスト | 確認項目 |
|:---|:---|
| **委譲先選定** | 適切な specialist に振り分けるか |
| **委譲理由** | 振り分け理由を説明できるか |
| **役割重複** | specialists の責務が混線していないか |

---

## 最小例: Reader（single）

```yaml
id: ts-reviewer
name: TypeScript レビュー
kind: single
description: TypeScript の読み取り専用レビュー
system_prompt: |
  あなたは TypeScript コードレビューの専門家です。

  対象:
  - workspace 内の TypeScript ファイル
  - 実装・型定義・周辺コメント

  対応しないこと:
  - ファイル変更
  - 外部 Web 調査
  - 推測だけに基づく断定

  進め方:
  1. file_read で関連ファイルを確認する。
  2. 型安全性、可読性、保守性の観点で問題点を抽出する。
  3. 根拠つきで優先度を分けて報告する。

  出力形式:
  - 概要
  - 指摘一覧
  - 推奨修正方針

  判断基準:
  - 型の抜け道を警戒する
  - 暗黙挙動より明示を優先する
  - 変更提案は最小差分を優先する
allowed_tools:
  - file_read
```

## 最小例: Router（orchestrator）

```yaml
id: doc-orchestrator
name: 文書処理オーケストレータ
kind: orchestrator
description: 依頼内容に応じて要約・レビューへ振り分ける
system_prompt: |
  あなたは文書処理のルータです。
  自分で詳細作業を抱え込まず、依頼を要約して最適な specialist に委譲します。

  委譲方針:
  - 要約・蒸留が中心なら distill に回す
  - 品質評価や欠落指摘が中心なら review に回す
  - 依頼が曖昧なら、必要最小限の前提を整理してから委譲する

  出力形式:
  - 依頼の要約
  - 委譲先
  - 委譲理由
allowed_tools:
  - file_read
specialists:
  - tool_name: consult_distill
    name: distill
    role_instructions: 文書やメモの要点抽出と再構成を担当する。
  - tool_name: consult_review
    name: review
    role_instructions: 文書品質、欠落、改善点の指摘を担当する。
```

---

## Instructions

- 生成前に [references/strands-yaml-schema.md](references/strands-yaml-schema.md) の制約を再確認する
- Strands で利用可能なツールだけを前提に YAML を設計する
- Claude Code のツール名・権限・発動方式は持ち込まない
- `system_prompt` には役割・対象・禁止事項・出力形式・判断基準を含める
- `allowed_tools` は最小権限で設計する
- Router は委譲基準を明示し、自分で抱え込みすぎない
- 保存後は、利用者に strands-py UI で **agent_id** と **mode** を選ぶよう案内する
- `agent_id` を選択して会話する場合、そのエージェントは KC スキルを自動選択して実行する仕組みではない
- KC スキル名を前提にせず、この YAML の `system_prompt` と `allowed_tools` に基づいて行動するよう設計する
```