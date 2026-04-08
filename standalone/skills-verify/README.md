# Skills Verification (Strands.multiagent)

`standalone/skills-verify` は、`KC-Dev-Agents-main/.agent/skills` を対象に
`strands.multiagent`（Graph）で連鎖実行・運用再実行・失敗時リカバリを検証する実行基盤です。

## 前提
- Python 実行環境はユーザ側で用意済み
- Bedrock モデルを使用
- `.env` は `standalone/.env` を利用（`load_dotenv()`）
- `MAX_TOKEN` は全ステップ固定で **8091**

## 必須環境変数
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_BEDROCK_MODEL_ID`
- `AWS_MAX_TOKENS`（固定値: `8091`）

## 実行（Windows）
`standalone/skills-verify/scripts` で実行:

```bat
python -X utf8 workflow.py --mode full
```

必要に応じてモード切替:

```bat
python -X utf8 workflow.py --mode chain-only
python -X utf8 workflow.py --mode recovery-only
```

## 出力
- `results/kc_skills_catalog.json`
- `results/kc_multiagent_summary.json`

## スクリプト構成
- `scripts/workflow.py`（本体エントリ）
- `scripts/util/common.py`（共通処理）
- `scripts/util/catalog.py`（skillsカタログ生成）
- `scripts/util/multiagent_graph.py`（Graph実装）

Graph 実行時の成果物:
- `skills-machine/20_notes/spec_distilled.md`
- `skills-machine/30_proposal/proposal.md`
- `skills-machine/40_decision_log/REV-*.json`
- `skills-machine/40_decision_log/REV-RERUN-*.json`

## 判定
- `summary.status` が `pass`
- `nodes.distillNode.status == success`
- `nodes.proposalNode.status == success`
- `nodes.reviewNode.status == success`
- 失敗時は `nodes.recoveryNode` と `failure.error_type` / `failure.retry_action` / `failure.recovery_output` を確認

## ノード責務分離 Version UP 判定基準
- `distillNode`: 入力は `testdata/doc.md`、出力は `skills-machine/20_notes/spec_distilled.md` のみ
- `proposalNode`: 入力は `20_notes/spec_distilled.md`、出力は `30_proposal/proposal.md` のみ
- `reviewNode`: 入力は `20_notes` + `30_proposal` + review 参照例、出力は `40_decision_log/REV-*.json` のみ
- `rerunReviewNode`: 入力は既存 `notes/proposal`、出力は `40_decision_log/REV-RERUN-*.json` のみ
- `recoveryNode`: 入力は `failed_stage` と `error`、出力は `error_type` と `retry_action` を含む復旧方針

## 成功判定ルール（厳密）
- 各ノードは `node error == none` かつ `期待成果物の存在 == true` のときのみ `success`
- `graph_results` は長文本文を保存せず、`stage/status/output_path/error` の機械可読形式で保存
- 失敗時 `failure` には `failed_stage` / `error_type` / `retry_action` / `error_message` を必ず出力

## 失敗時の確認順序
1. `.env` の `AWS_*` 必須項目を確認
2. Windows では `python -X utf8` で実行
3. token 超過時は出力制約（文字数・章数）を強める
4. `file_read` / `file_write` の対象パスを確認

