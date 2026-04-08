---
name: pdf-convert
description: >
  PDF / DOCX / PPTX 等のドキュメントを高品質な Markdown に変換し、案件の inbox に配置する。
  Docling（ローカル実行）によるテーブル・数式・コード認識、OCR 対応。
  Use when user says「PDFを変換して」「inboxに取り込んで」「ドキュメントをMarkdownにして」
  「RFPをMarkdownに変換して」「顧客資料を変換して」「OCRで変換して」「一括変換して」。
  Do NOT use for: Markdown → PDF の逆変換（→ md-to-pdf）、
  知識の蒸留・構造化（→ distill）、スライド変換（→ slide-gen）。
allowed-tools: "Bash(python:*)"
metadata:
  author: KC-Prop-Foundry
  version: 1.3.0
  category: document-conversion
---

# Skill: PDF → Markdown 変換 (pdf-convert)

> **構造を読み解き、知識を取り込む — すべてはテキストから始まる**

CRITICAL: 本スキル実行時は、対象案件の `projects/<案件名>/` を明示すること。

## Instructions

**Strands（strands-py）**: Bash やローカル python 一発実行ではなく、ツール **`pdf_convert_to_inbox`** を使う。出力は workspace の **`inbox/`**。詳細は [references/strands-py-runtime.md](references/strands-py-runtime.md)。

### ワークフロー内の位置

```
顧客 PDF/DOCX/PPTX → [pdf-convert] → distill → 成果物作成
                           ↓
               projects/<案件名>/10_inbox/*.md
```

### プロジェクトディレクトリ構造

| 番号 | ディレクトリ | 本スキルとの関係 |
|:---|:---|:---|
| **10** | `10_inbox/` | 変換した Markdown の出力先 |
| **20** | `20_notes/` | 後続の distill スキルが蒸留結果を配置 |
| **40** | `40_decision_log/` | 変換時の判断（OCR 精度、手動修正等）を記録 |

### 入力

| 形式 | 構造認識 | OCR | 備考 |
|:---|:---|:---|:---|
| PDF（テキスト） | テーブル・数式・コード | — | 最も一般的 |
| PDF（スキャン） | テーブル | `--ocr` 必須 | 紙スキャン文書 |
| DOCX | テーブル | — | 議事録・仕様書 |
| PPTX | スライド | — | プレゼン資料 |
| XLSX | テーブル | — | データ定義書 |
| HTML | 構造 | — | Web ページ |
| PNG/JPG/TIFF/BMP | — | `--ocr` 推奨 | ホワイトボード写真等 |

### 出力

```markdown
---
source: "元のファイル名.pdf"
converted_at: "2026-02-11T12:30:00.000000"
converter: "docling"
---

# ドキュメントタイトル

（変換されたコンテンツ）
```

出力先: `projects/<案件名>/10_inbox/<元ファイル名>.md`

---

## Step 1: 変換前の確認

**チェックリスト**:
- [ ] ファイル形式は対応形式か（PDF, DOCX, PPTX, XLSX, HTML, 画像）
- [ ] ファイルはパスワード保護されていないか
- [ ] PDF の場合: テキスト選択が可能か（不可能なら `--ocr` が必要）
- [ ] ファイルサイズが極端に大きくないか（100MB 以上は分割を検討）
- [ ] 対象の案件ディレクトリ（`projects/<案件名>/`）が存在するか
- [ ] 10_inbox/ ディレクトリが存在するか（なければ作成）

### 判断フロー

```
ファイル受領
  ├── テキスト選択可能？ → Yes → 通常変換（Step 2a）
  │                    → No  → OCR 変換（Step 2b）
  ├── 複数ファイル？   → Yes → 一括変換（Step 2c）
  └── 特殊要件？       → テーブルが重要 → デフォルト（テーブル認識 ON）
                       → 速度重視     → --no-tables オプション
                       → 高精度要求   → VLM モード（Step 2d）
```

---

## Step 2a: 通常の単一ファイル変換

```bash
python scripts/convert_to_md.py <ファイルパス> --project <案件名>
```

例:
```bash
python scripts/convert_to_md.py "C:\Downloads\RFP_教育データ基盤.pdf" --project education-data-platform
```

**チェックリスト**:
- [ ] 正しいファイルパスを指定したか
- [ ] 案件名が正しいか
- [ ] 変換が正常に完了したか（エラーメッセージなし）

---

## Step 2b: OCR 変換（スキャン PDF / 画像）

```bash
python scripts/convert_to_md.py <ファイルパス> --project <案件名> --ocr
```

注意: OCR は処理時間が長い（ページ数に依存）。テキスト埋め込み済みの PDF には `--ocr` を使用しないこと。

**OCR 精度の事前見積もり**:

| 入力品質 | 期待精度 | 推奨アクション |
|:---|:---|:---|
| 300dpi 以上、明瞭な印刷物 | 95%+ | 通常 OCR で十分 |
| 200dpi、一般的なスキャン | 85-95% | OCR + 手動補正 |
| 低解像度、手書き混在 | 70-85% | VLM モード推奨、大幅な手動補正が必要 |
| 写真撮影、歪みあり | 50-70% | 再スキャン推奨。やむを得ない場合は VLM |

**チェックリスト**:
- [ ] テキスト選択不可であることを確認したか
- [ ] 画像の解像度は十分か（300dpi 推奨）
- [ ] OCR 変換が完了したか
- [ ] 変換結果を目視でサンプリング確認したか

---

## Step 2c: 一括変換（ディレクトリ）

```bash
python scripts/convert_to_md.py <ディレクトリパス> --project <案件名>
```

### 一括変換の管理

```
変換対象: 12 ファイル
  ├── PDF（テキスト）: 8 件 → 通常変換
  ├── PDF（スキャン）: 2 件 → OCR 変換
  ├── DOCX: 1 件 → 通常変換
  └── PPTX: 1 件 → 通常変換
```

一括変換後は、各ファイルのサマリーを出力する:

| ファイル | 状態 | ページ数 | 要確認 |
|:---|:---|---:|:---|
| RFP_v2.pdf | 成功 | 45 | — |
| 仕様書.pdf | 成功 | 120 | テーブル 3 箇所 |
| 議事録.docx | 成功 | 5 | — |
| スキャン資料.pdf | 要確認 | 30 | OCR 精度低（手書き） |

**チェックリスト**:
- [ ] 対象ディレクトリの全ファイルを列挙したか
- [ ] テキスト/OCR の振り分けが正しいか
- [ ] 変換サマリーを確認したか
- [ ] 「要確認」のファイルを個別に品質チェックしたか

---

## Step 2d: VLM 高精度変換

Docling の VLM（Vision Language Model）パイプラインを使用して高精度変換を行う。

```bash
docling --pipeline vlm --vlm-model granite_docling <ファイルパス>
```

**使用する場面**:
- スキャン品質が低く通常 OCR では不十分
- 図表内のテキストを高精度で読み取りたい
- 複雑なレイアウト（段組み、テキストボックス）のある文書

**チェックリスト**:
- [ ] 通常 OCR で不十分であることを確認したか
- [ ] VLM モデル（granite_docling）がインストール済みか
- [ ] VLM 変換の結果が通常 OCR より改善されたか

---

## Step 3: 変換結果の品質確認

**チェックリスト**:
- [ ] 文書の見出し階層（#, ##, ###）が正しいか
- [ ] テーブルの列数・行数が元文書と一致するか
- [ ] 数式・コードブロックが正しく変換されているか
- [ ] 図表のキャプションが正しく抽出されているか
- [ ] ページ番号・ヘッダー・フッターが混入していないか
- [ ] 文字化け・文字欠けがないか
- [ ] 箇条書きのインデントが保持されているか
- [ ] フロントマター（source, converted_at, converter）が正しいか

### よくある修正パターン

| 現象 | 原因 | 対処 | 修正マーキング |
|:---|:---|:---|:---|
| テーブルの列ズレ | 複雑なセル結合 | 手動で Markdown テーブルを修正 | `<!-- fixed: merged cell -->` |
| ヘッダー/フッター混入 | PDF のレイアウト認識 | 該当行を削除 | `<!-- removed: header/footer -->` |
| 数式の文字化け | 特殊フォントの未認識 | LaTeX 形式で再記述 | `<!-- fixed: formula -->` |
| 箇条書きの崩れ | インデント認識の限界 | 手動でインデントを修正 | — |
| 縦書きテキストの誤認識 | 横書き前提の解析 | 手動で修正、元文書を参照 | `<!-- fixed: vertical text -->` |
| 図中テキストの欠落 | 図が画像として処理 | VLM で再変換 or 手動追記 | `<!-- added: figure text -->` |

手動修正箇所には HTML コメントでマーキングし、後続の distill スキルが修正箇所を認識できるようにする。

---

## Step 4: メタデータ整備

変換結果のフロントマターを確認・補完する。

### 必須メタデータ

```yaml
---
source: "元のファイル名.pdf"
converted_at: "2026-02-11T12:30:00.000000"
converter: "docling"
pages: 45                    # 元文書のページ数
tables: 12                   # テーブル数
manual_fixes: 3              # 手動修正箇所数
ocr: false                   # OCR 使用の有無
confidence: "high"           # 変換品質の自己評価（high/medium/low）
---
```

### 品質ラベルの基準

| ラベル | 基準 | 後続の distill への影響 |
|:---|:---|:---|
| **high** | 手動修正なし、テーブル・数式正常 | そのまま蒸留可能 |
| **medium** | 手動修正 1-5 箇所、軽微な品質問題 | 修正箇所を注意して蒸留 |
| **low** | 手動修正 5+ 箇所、OCR 精度問題 | 元文書との照合を推奨 |

**チェックリスト**:
- [ ] フロントマターの全フィールドが記入されているか
- [ ] pages/tables の数値が元文書と一致するか
- [ ] manual_fixes の数が手動修正の実数と一致するか
- [ ] confidence ラベルが品質を正確に反映しているか

---

## Step 5: 後続スキルへの引き渡し確認

変換・品質確認・メタデータ整備が完了したら、後続の distill スキルに引き渡す。

### 引き渡しチェック

| 確認項目 | 基準 | 不合格時の対応 |
|:---|:---|:---|
| 全ファイルが 10_inbox/ に配置 | 漏れなし | 変換漏れファイルを Step 2 で再処理 |
| フロントマター完備 | 全ファイル | Step 4 を再実施 |
| confidence: low のファイル | 0 件が理想 | 元文書との照合 or VLM 再変換 |
| テーブルの品質 | 列数・行数一致 | 手動修正 |
| 変換サマリー | 作成済み | サマリーを作成 |

### 引き渡し時の指示テンプレート

```
「distill スキルで、10_inbox/ の資料を 20_notes/ に蒸留して」

補足情報:
- 変換ファイル数: X 件
- confidence: high Y 件 / medium Z 件
- 手動修正箇所: [ファイル名] の [箇所] を修正済み（<!-- fixed: ... --> マーク付き）
- 特記事項: [あれば記載]
```

**チェックリスト**:
- [ ] 引き渡しチェックの全項目がパスしたか
- [ ] confidence: low のファイルが解消されたか
- [ ] 変換サマリーが作成されたか
- [ ] distill への引き渡し指示が準備できたか

---

## Step 6: 変換レポート生成

一括変換や大規模変換の場合、変換結果のレポートを生成する。

### レポート構造

```markdown
# PDF → Markdown 変換レポート

## メタ情報
- 案件名: <案件名>
- 変換日: YYYY-MM-DD
- 変換ファイル数: X 件
- 総ページ数: Y ページ

## 変換結果サマリー

| 状態 | 件数 | 割合 |
|:---|---:|---:|
| 成功（high） | X | Y% |
| 要確認（medium） | X | Y% |
| 要修正（low） | X | Y% |
| 失敗 | X | Y% |

## ファイル別詳細
（各ファイルの変換状態・品質・修正内容）

## 特記事項
（変換時に発見した問題・判断事項）
```

### ドキュメント変換 Slop 防止チェック（Distributional Convergence 対策）

ドキュメント変換は「元文書の構造を忠実に再現する」ことが本質であり、変換器やエージェントが元文書を無視して画一的な Markdown 構造に均してしまうと、後続の蒸留・分析で情報損失が発生する。

| # | 変換 Slop パターン | 検出方法 | 対策 |
|:---|:---|:---|:---|
| PC-1 | **見出し階層の画一化** — 元文書の構造に関わらず `# → ## → ###` の3階層に均してしまう | 元 PDF の目次・見出し階層と変換後の Markdown 見出しを比較し、深さ・順序が一致するか確認する | 元文書の見出し構造を忠実に再現する。4階層以上あれば4階層で出力し、2階層しかなければ2階層で出力する |
| PC-2 | **テーブル構造の単純化** — セル結合・入れ子テーブル・注釈行を無視し、常に単純なパイプ区切りテーブルに変換する | 元文書のテーブルと変換後テーブルの列数・行数・セル結合パターンを照合する | セル結合は HTML コメントで注記（`<!-- merged: 3 cols -->`）。注釈行や小計行は構造を維持し、必要に応じて HTML テーブルで表現する |
| PC-3 | **図表コンテキストの消失** — 図表のキャプション・凡例・前後の説明文を落とし、画像リンクだけを残す | 元文書で図表に付随するキャプション・凡例・参照テキストが変換後に存在するか確認する | 図表のキャプション（`Figure 1: ...`）、凡例、前後の説明文を明示的に保持する。画像として処理された図には `<!-- figure: [元のキャプション] -->` を付記する |
| PC-4 | **メタデータのテンプレート埋め** — confidence を常に `high`、manual_fixes を常に `0` としてデフォルト値で埋めてしまう | フロントマターの値が実際の変換結果（手動修正箇所数、OCR 精度）と整合しているか検証する | 変換結果を実際に検査してからメタデータを記入する。手動修正を1箇所でも行った場合は manual_fixes を正確にカウントし、confidence を実態に合わせて設定する |

> **核心原則**: **原文書の忠実な鏡像** — 変換結果は元文書の構造・情報・文脈を映し出す鏡でなければならない。「別の PDF を変換しても同じ Markdown 構造になるか？」→ なるなら変換 Slop である。

**チェックリスト**:
- [ ] 全ファイルの変換結果がレポートに含まれているか
- [ ] 成功/要確認/要修正/失敗の分類が正しいか
- [ ] 特記事項に判断事項を記録したか
- [ ] 変換 Slop チェック（PC-1〜PC-4）に 2 つ以上該当しない
- [ ] 出力がドメイン固有の要素を含み、汎用テンプレートに見えない

---

## Advanced Options

### Docling CLI の直接利用

```bash
docling input.pdf              # 基本変換
docling input.pdf --to md      # Markdown 出力
docling input.pdf --to json    # JSON（ロスレス）
docling --pipeline vlm --vlm-model granite_docling input.pdf  # VLM 高精度変換
```

### Python API

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("path/to/file.pdf")
markdown = result.document.export_to_markdown()
```

---

## Examples

### Example 1: RFP の変換

```
「pdf-convert スキルで、顧客から受領した RFP.pdf を education-data-platform の inbox に変換して」

→ Step 1: PDF を確認 — テキスト選択可能、45 ページ、テーブル 12 箇所
→ Step 2a: python scripts/convert_to_md.py "RFP.pdf" --project education-data-platform
→ Step 3: テーブル品質を重点チェック。セル結合 2 箇所を手動修正
→ Step 4: フロントマター記入（pages: 45, tables: 12, manual_fixes: 2, confidence: high）
→ Step 5: distill への引き渡し確認
→ 出力: projects/education-data-platform/10_inbox/RFP.md
```

### Example 2: 顧客資料フォルダの一括変換

```
「pdf-convert スキルで、C:\Downloads\顧客資料\ フォルダを education-data-platform に一括変換して」

→ Step 1: ディレクトリ内のファイルを列挙（PDF 8件, DOCX 2件, PPTX 1件）
→ Step 2c: 一括変換を実行。OCR 必要なスキャン PDF 2件を振り分け
→ Step 3: 各ファイルの変換品質をサンプリングチェック
→ Step 4: 全ファイルにメタデータを付与
→ Step 6: 変換レポートを生成（成功 9件, 要確認 2件）
→ 出力: projects/education-data-platform/10_inbox/ に 11 ファイル + 変換レポート
```

### Example 3: スキャン文書の OCR 変換

```
「pdf-convert スキルで、紙スキャンの仕様書を OCR で変換して inbox に配置して」

→ Step 1: PDF を確認 — テキスト選択不可（画像ベース）、200dpi スキャン
→ Step 2b: --ocr オプションで変換実行
→ Step 3: OCR 結果を通読。固有名詞・数値の誤認識 5 箇所を手動補正
→ Step 4: confidence: medium、manual_fixes: 5 を記録
→ Step 5: 元文書との照合が必要な箇所を補足情報として記載
→ 出力: projects/<案件名>/10_inbox/仕様書.md（修正箇所マーキング済み）
```

### Example 4: 複数ファイル一括変換

```
「inbox にある PDF を全て Markdown に変換して」

→ Step 1: 対象ディレクトリ内のファイル一覧を取得し、対応形式をフィルタリング
→ Step 2c: 一括変換を実行。テキスト/OCR を自動振り分け
→ Step 3: 変換結果を 1 ファイルずつ確認。テーブル崩れ・見出し階層の異常をサンプリングチェック
→ Step 4: 変換失敗したファイルがあれば個別に再実行（OCR or VLM）
→ Step 6: 変換サマリー（成功/失敗/要確認）をレポート出力
→ 結果: 全ファイルが 10_inbox/ に配置され、変換レポートを報告
```

### Example 5: 表が多い仕様書の変換

```
「この RFP には複雑な表が多い。テーブルを崩さず変換して」

→ Step 1: PDF を開き、テーブルの複雑さを事前確認（セル結合・入れ子テーブル・縦書きヘッダー等）
→ Step 2a: テーブル認識 ON（デフォルト）で変換実行
→ Step 3: 変換後の Markdown テーブルを元 PDF と並べて照合。列数・行数・数値の一致を重点チェック
→ Step 3: セル結合崩れや列ズレが検出された箇所を手動修正（<!-- fixed: merged cell --> 付記）
→ Step 4: tables: 15, manual_fixes: 4, confidence: medium を記録
→ Step 5: data-validation スキルでテーブルデータの整合性を最終検証
→ 結果: テーブル構造が元文書と一致した高品質な Markdown。修正箇所は明示的にマーキング済み
```

### Example 6: スキャン PDF の VLM 高精度変換

```
「紙をスキャンした PDF です。OCR で変換して」

→ Step 1: PDF を確認 — テキスト選択不可（画像ベース）。解像度が低い場合は再スキャンを推奨
→ Step 2b: 通常 OCR で変換を試行
→ Step 3: OCR 結果を確認。誤認識が多い（精度 80% 未満と推定）場合は VLM 再変換を判断
→ Step 2d: VLM モード（--pipeline vlm）で再変換し、精度を比較
→ Step 3: 最終的な Markdown を手動補正。固有名詞・数値・表の内容を元文書と照合
→ Step 4: confidence: medium、OCR 方式と補正内容をメタデータに記録
→ 結果: OCR 変換された Markdown が inbox に配置。補正済み箇所と信頼度が低い箇所をコメントで明示
```

---

## Troubleshooting

| 問題 | 原因 | 解決策 |
|:---|:---|:---|
| `ModuleNotFoundError: docling` | 未インストール | `pip install docling` |
| 初回実行が遅い | ML モデルダウンロード中 | 初回のみ。1-5 分待機 |
| テーブルが崩れる | 複雑なセル結合・入れ子 | 手動修正、または VLM で再試行 |
| OCR 文字化け | 低品質スキャン | 高解像度再スキャン、VLM モデル試行 |
| `案件が見つかりません` | 存在しない案件名 | `ls projects/` で確認。`_template` からコピー |
| メモリ不足 | 大規模 PDF（100MB+） | ファイルを分割して変換 |
| docling のバージョン不整合 | v2.70 未満のバージョン | `pip install --upgrade docling>=2.70.0` |
| Office 365 形式の DOCX が崩れる | 新しい XML スキーマ | docling を最新版に更新、それでも崩れる場合は PDF 経由で変換 |
| 文字エンコーディングの問題 | Shift_JIS 等の非 UTF-8 | ファイルを UTF-8 に変換してから処理 |
| 縦書き文書の認識精度が低い | 横書き前提の解析エンジン | VLM モードで再変換、手動補正を前提とする |
| 大ファイルで変換が途中停止する | タイムアウト or メモリ | ページ範囲を指定して分割変換 `docling input.pdf --pages 1-50` |

---

## Security Notes

- Docling はすべてローカルで処理。顧客の機密 PDF が外部サーバーに送信されることはない
- VLM 使用時: `granite_docling` モデルもローカル動作。クラウド VLM 使用時は機密性に注意

## References

| ファイル | 内容 |
|:---|:---|
| [docling-configuration.md](references/docling-configuration.md) | Docling 設定リファレンス（CLI オプション、Python API 設定、ドキュメント種別ごとの最適設定、テーブル抽出モード、OCR 言語設定、バッチ処理） |
| [format-compatibility.md](references/format-compatibility.md) | 入力フォーマット互換性マトリクス（PDF/DOCX/PPTX/XLSX/HTML/画像の機能対応表、制限事項、変換精度、文字化け対策、エンコーディング診断フロー） |
| [post-processing-guide.md](references/post-processing-guide.md) | 変換後処理ガイド（品質改善手順、テーブル整形パターン、画像パス管理、ヘッダー/フッター除去、ページ番号処理、目次再構成、最終品質チェックリスト） |

---

## Related Files

| ファイル | 役割 |
|:---|:---|
| `scripts/convert_to_md.py` | 変換スクリプト本体 |
| `requirements.txt` | Python 依存定義（`docling>=2.70.0`） |
| `.agent/workflows/convert-pdf.md` | エージェントワークフロー定義 |

## Related Skills

| スキル | 関係 | 説明 |
|:---|:---|:---|
| **distill** | 後続 | `10_inbox/` の Markdown を `20_notes/` に蒸留 |
| **review** | 検証 | 変換結果の品質をレビュー |
| **data-validation** | 検証 | テーブルデータの整合性チェック |
