### strands-py
> Backend(Fast API + Strands Agents SDK)、Frontend(Vite)を利用した、マルチエージェントWebアプリケーション

### Agent の Workspace
> 以下のフォルダでのみ、file_read、file_writeといったツール実行を行う
```
backend/ data / projects / default
```
#### スキルとポリシー


スキルツリーはプロジェクトの **`team_context`**（`.strands-project.json`）に応じて解決される。`developer` → `backend/agent/skills/dev`、それ以外（`marketing` / `hr` / `pmo` / `engineering`）→ `backend/agent/skills/pr`。Strands ではフィルタ後に **AgentSkills** で読み込む。**主な利用モードは UI の「スキル（1エージェント）」でエージェント選択を空にした状態**

Team 文脈（`skills/pr`）ではスキル本文に Claude Code 前提の記述が多く、Strands ですべてがすぐに意図どおり動くとは限りません。

##### `.strands-project.json`（プロジェクト直下）

| フィールド | 内容 |
|-----------|------|
| `display_name` | プロジェクト一覧の表示名（日本語可）。省略や欠損時は API が `project_id` を使う。 |
| `team_context` | `developer` / `marketing` / `hr` / `pmo` / `engineering`。欠損や未知の値は **`developer`** に正規化（パース可能な JSON のみ）。 |

**Skills ルート対応**: `developer` → `backend/agent/skills/dev`、上記 Team ID のいずれか → `backend/agent/skills/pr`。

`backend/src/infrastructure/skill_policy.py` の `SKILL_POLICIES` で次を上書きする。`WIRED_SKILL_ADAPTERS` に載る adapter は strands-py で代替手段あり（`GET /api/skills/catalog` の `adapter_wired` を参照）。

| スキル ID | ランタイムに載るか | adapter | adapter 接続 |
|-----------|-------------------|---------|----------------|
| agent-craft | いいえ（除外） | なし | 不要 |
| skill-forge | いいえ（除外） | なし | 不要 |
| pdf-convert | はい | pdf_convert_backend_tool | 接続済み（compat ツール） |
| diagram | はい | diagram_write_mapping | 接続済み（compat ツール） |

上記以外のディレクトリは `policy_for` のデフォルト（載せる・adapter なし）になる。

##### pdf-convert / diagram と Strands ツール（KC スキル本文との差）

KC の SKILL は Bash や `10_inbox` 等の番号付きディレクトリを参照することがある。strands-py のプロジェクト workspace は `inbox`, `notes`, `proposal`, `decision` を主に使う。次の **compat ツール**（`backend/src/infrastructure/compat_tools.py`）を優先する。

| KC スキル | Strands ツール | 入力 | 出力先（workspace 相対） |
|-----------|----------------|------|---------------------------|
| pdf-convert | `pdf_convert_to_inbox` | `input_path`（絶対パスまたは inbox 相対）、任意 `output_filename`、`ocr`（互換用フラグ） | `inbox/*.md`（Docling 変換。未インストール時は JSON で partial_success） |
| diagram | `diagram_generate_drawio` | `diagram_brief`（図の要件テキスト）、`output_filename`（既定 `architecture.drawio`）、`title` | `proposal/*.drawio`（配下のみ）。成功時の戻り値は言語タグ xml のフェンス内に `<mxfile>` から始まる本文のみ（説明文なし） |

各スキルディレクトリの `references/strands-py-runtime.md` に運用上の注意がある。

compat ツールに `brave_web_search`（Brave Search API）がある。`backend/.env` の `BRAVE_API_KEY` を設定すると利用可能。`web_fetch_text` は既知 URL の取得用。

バックエンド起動後、ディスク上の全スキルと解決後ポリシーは `GET /api/skills/catalog` で取得できる。クエリ **`project_id`** を付けるとそのプロジェクトのメタに基づきルートを解決する。省略時は **developer 相当**（`skills/dev`）で返す（移行互換）。

環境変数 **`STRANDS_DEBUG_PROJECT_CONTEXT`** を `1` / `true` 等にすると、`project_id` / `team_context` / 解決後 `skills_root` を debug ログに出す。

`.strands-project.json` が **JSON として壊れている**場合、チャット・カタログ等は **422** でエラーになる。`GET /api/projects` では当該項目に **`meta_error`** と **`detail`** が付く。

#### チャットモード（UI）

`team_context` が **`developer`** のプロジェクトでは、モードボタンは **通常（Skillなし）→ スキル（自動選択）→ Workflow → Swarm → 通常** の順で循環する。`team_context` がそれ以外のときは **Workflow を出さず**、**通常 → スキル → Swarm → 通常** とする（切り替え時に workflow が残らないよう UI でも落とす）。

`POST /api/chat` の `mode` は UI からは `default` / `skills` / `workflow`（Developer プロジェクトのみ）/ `swarm` を送る。

`mode=orchestrate`（オーケストレータ + specialist）は **API 互換のためバックエンドに残す**が、プロダクト上は非推奨とし UI では選べない。`workspace/.../agents/` に `kind: orchestrator` の YAML を置けるが、一覧 API（`GET /api/agents`）の応答からも除外する。

モード「スキル（自動選択）」で Workspace の `agents/*.yaml` を複数参照（参照ボタン）し、重複排除後に 2 件以上ある場合は `POST /api/chat/agents-multi` に送り、選択した YAML 定義に基づく Strands Swarm で処理する（本文の `message` と `agent_ids`、SSE は `POST /api/chat` の Swarm と同形式）。Swarm モードで `agents` の YAML を複数参照した場合は送信せずモーダルで案内する。

プロジェクトは **ID**（`data/projects/<id>/` のディレクトリ名、`^[a-zA-Z0-9._-]+$`）と **表示名**（日本語可）、**`team_context`** を分離する。`.strands-project.json` に `display_name` と `team_context` を保存する。`GET /api/projects` / `POST /api/projects`（任意の `display_name` / `team_context`）/ **`PATCH /api/projects/{id}`** で更新可能。メタが無い既存フォルダは表示名が ID と同じ、`team_context` は **`developer`** として返る。

**workflow** モード（`POST /api/chat` の `mode=workflow`）は **`team_context` が `developer` のプロジェクトのみ**利用可能。それ以外は **403**（`detail.code`: `workflow_requires_developer`）。

ワークフロー定義 Markdown は **`backend/agent/workflows/dev`** を参照する。

#### 実行環境(開発者環境)
|実行環境|Version|
|------|-------|
|Python（サーバサイド）|3.13|
|node（フロントエンド）|22.20.0|
#### 実行手順
backend 
```bash
cd backend
pip install -r requirements.txt
python main.py
```

初回起動時、各 `team_context` 用のサンプルプロジェクト（`team-developer` 等）が `data/projects/` に無ければ作成される。自動テスト（pytest）では環境変数 **`STRANDS_SKIP_SEED_PROJECTS=1`** で無効化される（`tests/conftest.py` で設定）。
frontend
```bash
cd frontend
npm install
npm run dev
```