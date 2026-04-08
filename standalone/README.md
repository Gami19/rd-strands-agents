# standalone/（検証・実験用）
このフォルダは、Strands Agents の理解や機能検証のための単体実験・サンプルコードをまとめた場所です。

## 構成（役割）
- `check/`
  - 環境・利用可能性の確認用スクリプト（例: `check_model.py`, `strands_tool_check.py`）
- `skills-verify/`
  - `KC-Dev-Agents-main` の `.agent/skills/*/SKILL.md` を、Strands Agents の `AgentSkills` で
    Discovery（読み込み）→ Activation（発動）する検証の受け皿
  - **起動・動作の前提**: `standalone/skills-verify` のワークフローは、スクリプトが参照する skills のパスが
    `<リポジトリルート>/KC-Dev-Agents-main/.agent/skills` に固定されています。
    そのため **`KC-Dev-Agents-main` を、このリポジトリのルート（`standalone/` と同じ階層）直下に配置**しないと
    起動時に skills ディレクトリが見つからず失敗します。
  - 現状、検証スクリプトの配置がまだのため、必要に応じて追加してください
- `experiments/`
  - MCP連携、マルチエージェント、Web検索、コード実行など、目的が独立した実験群
- `misc_scripts/`
  - `Agent`/`strands_tools` を使った単発スクリプト（例: `simple.py`, `file-operation.py` など）

## 設定
- 必要に応じて `.env.example` を参考に `.env` を用意してください

## 進め方の目安
1. まずは `skills-verify/` で「Skills 機構（Discovery/Activation）」が成立するか確認する
2. 必要になったら、対応ツール（例: `file_read`, `shell`）や resource 参照まで検証範囲を広げる
3. それ以外の実験は `experiments/` 配下の README を参照する