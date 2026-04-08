# strands-py エージェント YAML スキーマ

strands-py バックエンドの `backend/src/infrastructure/agent_definitions.py` が検証する内容の要約。詳細はソースが正とする。

## 共通

- 保存場所: プロジェクト workspace の `agents/<agent_id>.yaml` または `.yml`。探索は `.yaml` 優先の実装あり。
- トップレベルは YAML map。
- オプション `id`: ファイル名の stem（正規化後）と一致させる。`^[a-zA-Z0-9._-]+$` に合う識別子を推奨。

## allowed_tools（必須）

次の **名前だけ**が許可される（サブセットを指定する）:

- `file_read`（**必ず含める**）
- `file_write`
- `pdf_convert_to_inbox`
- `diagram_generate_drawio`
- `web_fetch_text`
- `brave_web_search`（Web 検索。`BRAVE_API_KEY` が必要）

上記以外の文字列は `unknown tools` でロード失敗。

## kind: single

`mode=skills` かつ UI で `agent_id` を選んだときに使用。

| フィールド | 必須 | 説明 |
|------------|------|------|
| kind | はい | `single` |
| name | はい | 表示名 |
| description | 任意 | 一覧 API 用 |
| system_prompt | はい | システムプロンプト |
| allowed_tools | はい | 上記ホワイトリスト、`file_read` 必須 |
| skills / allowed_skills | 任意 | 指定時は **高々 1 件**（1 スキル = 1 エージェント）。複数指定でロード失敗。 |
| department | 任意 | 一覧 API・UI の部門ラベル（`GET /api/agents`） |
| icon_key | 任意 | 一覧 API 用の装飾キー（将来拡張） |

## kind: orchestrator

`mode=orchestrate` かつ UI で `agent_id` を選んだときに使用。

single のフィールドに加え:

| フィールド | 必須 | 説明 |
|------------|------|------|
| kind | はい | `orchestrator` |
| specialists | はい | 1 件以上の配列 |

各 specialist 要素:

| フィールド | 必須 | 説明 |
|------------|------|------|
| tool_name | はい | `^[a-z_][a-z0-9_]*$`、オーケストレータが呼ぶツール名。重複不可 |
| name | はい | specialist の表示用ラベル |
| role_instructions | はい | specialist の system 相当の指示 |

## kind: swarm

一覧 API では `kind: swarm` をメタとして読める場合があるが、**YAML から Swarm 構成を組み立てる経路は strands-py の実装次第**である。本スキルでは主に **single / orchestrator** の生成を扱い、swarm は必要なら実装確認のうえで別途設計する。

## よくあるエラー

- `allowed_tools に file_read を含めてください`
- `unknown tools in allowed_tools: ...` → ホワイトリスト外の名前を削除
- `specialists[N].tool_name は ^[a-z_][a-z0-9_]*$` → 先頭は英小文字、アンダースコア可
- `mode=skills + agent_id では kind=single の YAML が必要` → orchestrator 用 YAML を skills で使っていないか確認
