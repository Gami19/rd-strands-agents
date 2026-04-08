# strands-py ランタイム（diagram）

KC 本スキルは VS Code Write や `30_proposal/` 等のパス表記が出てくる。**strands-py** では次のツールを使う。

## 使用ツール

- **`diagram_generate_drawio`**（compat ツール）

### 引数

- `diagram_brief`: 図に含める要素・関係を自然言語または箇条書きで渡す。
- `output_filename`: 既定 `architecture.drawio`。`.drawio` 拡張子に正規化される。
- `title`: 図のタイトル（XML 内の表題）。

### 出力

- **`proposal/`** 配下にのみ保存可能（パストラバーサル不可）。KC の `30_proposal/` に近い役割。
- ツールの**戻り値**（成功時）: 説明文なし。言語タグ `xml` のフェンス内に `<mxfile>` から始まる XML のみ。失敗時は従来どおり JSON（`partial_success` 等）。

### 品質

- 生成 XML は簡易テンプレートに基づく。複雑な図は brief を分割するか、`file_write` で手直しする運用も可（エージェントの allowed_tools に含まれる場合）。

## 運用上の注意

- 本 SKILL 内の Claude / VS Code **Write** 直接保存手順の代わりに **`diagram_generate_drawio`** を呼ぶ。
- 出力先を `notes` や `decision` に変えたい場合は、生成後に `file_read` / `file_write` で移動する（ポリシーとパス制限に従う）。
