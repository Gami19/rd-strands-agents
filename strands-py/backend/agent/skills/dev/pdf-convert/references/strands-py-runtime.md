# strands-py ランタイム（pdf-convert）

KC 本スキルは Bash + Docling ローカル実行を前提とした記述が多い。**strands-py** では次のツールを使う。

## 使用ツール

- **`pdf_convert_to_inbox`**（compat ツール）

### 引数

- `input_path`: 入力ファイル。workspace ルートからの相対パス、または絶対パス。対応拡張子は実装の `SUPPORTED_DOC_EXTS` に従う（PDF / DOCX / PPTX 等）。
- `output_filename`: 省略可。指定時はファイル名のみ有効。省略時は `<元stem>.md`。
- `ocr`: ブール。互換のため受け付けるが、現行実装では Docling 側の詳細設定は未接続のことがある。

### 出力

- **`inbox/`** 配下に Markdown を保存（KC の `10_inbox/` 相当の位置づけ）。フロントマターに `source` / `converted_at` / `converter: docling`。

### 依存

- Python パッケージ **docling**（`requirements.txt` に含まれる想定）。未インストールや変換失敗時はツールが JSON の `partial_success` と `next_actions` を返す。

## 運用上の注意

- 本 SKILL 内の `Bash(python:*)` 手順は **実行しない**。モデルは `pdf_convert_to_inbox` を呼ぶ。
- プロジェクトの作業領域は strands-py の `DATA_ROOT/projects/<project_id>/`（`inbox`, `notes`, …）。
