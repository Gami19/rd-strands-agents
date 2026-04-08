# 起動時シード用プロジェクト定義

`python main.py`（FastAPI lifespan）で `ensure_seed_team_projects()` が走ると、`data/projects/<project_id>/` が未作成なら workspace とメタを作り、続けて **このディレクトリ配下の `agents/*.yaml` を workspace の `agents/` に冪等コピー**する。

レイアウト（`project_id` は `seed_projects.py` の `SEED_TEAM_PROJECTS` と一致）:

- `team-developer/` … `developer` 用（エージェント YAML は置かない想定）
- `team-marketing/agents/` … Marketing Team 用エージェント
- `team-hr/agents/` … HR
- `team-pmo/agents/` … PMO
- `team-engineering/agents/` … Engineering

`team_context` が同じ **任意の** プロジェクト（例: ユーザーが新規作成した marketing プロジェクト）に対しても、`seed_team_agents_if_needed` は `team-<context>/agents/` をコピー元として同様にコピーする。
