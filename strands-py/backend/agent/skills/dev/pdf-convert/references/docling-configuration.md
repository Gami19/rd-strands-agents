# Docling 設定リファレンス

> Docling の主要パラメータ、ドキュメント種別ごとの最適設定、テーブル抽出・OCR・バッチ処理の設定ガイド

---

## 1. 主要設定パラメータ

### CLI オプション一覧

| オプション | デフォルト | 説明 |
|:---|:---|:---|
| `--to` | `md` | 出力形式（`md` / `json` / `text` / `doctags`） |
| `--ocr` | `false` | OCR を有効化（スキャン PDF・画像向け） |
| `--no-ocr` | — | OCR を明示的に無効化 |
| `--pipeline` | `standard` | 変換パイプライン（`standard` / `vlm`） |
| `--vlm-model` | — | VLM モデル名（`granite_docling` 等） |
| `--no-tables` | `false` | テーブル構造認識を無効化（速度重視時） |
| `--pages` | 全ページ | ページ範囲指定（例: `--pages 1-50`） |
| `--output` | カレントディレクトリ | 出力先ディレクトリ |

### Python API の主要設定

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat

# Pipeline options for PDF
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False                    # OCR on/off
pipeline_options.do_table_structure = True          # Table recognition on/off
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # ACCURATE or FAST

# Format options
pdf_format_options = PdfFormatOption(
    pipeline_options=pipeline_options
)

# Converter with options
converter = DocumentConverter(
    format_options={InputFormat.PDF: pdf_format_options}
)

result = converter.convert("input.pdf")
markdown = result.document.export_to_markdown()
```

---

## 2. ドキュメント種別ごとの最適設定

### PDF（テキスト埋め込み）

```bash
# Standard: most common case
docling input.pdf --to md

# With high-accuracy table recognition
docling input.pdf --to md
# (table recognition is enabled by default in ACCURATE mode)
```

```python
# Python API
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

**最適設定のポイント**:
- OCR は不要（テキストが埋め込まれているため）
- テーブル認識は ACCURATE モードを推奨
- 数式が多い場合は変換後の手動補正を見込む

### PDF（スキャン / 画像ベース）

```bash
# OCR enabled
docling input.pdf --to md --ocr

# VLM for low-quality scans
docling --pipeline vlm --vlm-model granite_docling input.pdf --to md
```

```python
# Python API with OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.lang = ["ja", "en"]  # Japanese + English
```

**最適設定のポイント**:
- `--ocr` 必須
- 日本語文書は `lang` に `ja` を含める
- 低品質スキャンは VLM パイプラインを検討
- 処理時間はテキスト PDF の 5-10 倍を見込む

### DOCX

```bash
docling input.docx --to md
```

**最適設定のポイント**:
- テーブル・箇条書き・見出しは高精度で変換される
- 画像は抽出されるが、テキストフローとの位置関係は再配置が必要な場合がある
- 変更履歴（Track Changes）は最終状態のみ変換される
- Office 365 の新しい XML スキーマに問題がある場合は docling を最新版に更新

### PPTX

```bash
docling input.pptx --to md
```

**最適設定のポイント**:
- 各スライドが `## Slide N` として見出し化される
- スライドノート（Notes）は本文の後に付記される
- SmartArt・図形内テキストの抽出精度は限定的
- アニメーション情報は失われる

### HTML

```bash
docling input.html --to md
```

**最適設定のポイント**:
- テーブル・リスト・見出し階層は高精度で変換
- CSS による視覚的構造（カラム、フロート等）は反映されない
- JavaScript で動的生成されるコンテンツは取得できない
- ローカルファイルまたは保存済み HTML を入力とする

---

## 3. テーブル抽出の設定と精度向上

### テーブル認識モード

| モード | 精度 | 速度 | 推奨場面 |
|:---|:---|:---|:---|
| **ACCURATE** | 高（セル結合対応） | 遅い | 仕様書・RFP・報告書（テーブルが重要） |
| **FAST** | 中（基本テーブル） | 速い | テーブルが少ない文書、速度重視 |
| **無効** (`--no-tables`) | — | 最速 | テーブルがない文書、テキストのみ必要 |

### テーブル精度向上のテクニック

| 問題 | 原因 | 対策 |
|:---|:---|:---|
| セル結合が崩れる | 複雑なマージセル | ACCURATE モード + 手動補正。`<!-- merged: N cols -->` で注記 |
| 列がズレる | 罫線なしテーブル | VLM パイプラインで再変換を試行 |
| ヘッダー行が本文に混入 | ヘッダー検出の失敗 | 手動で Markdown テーブルのヘッダー行を修正 |
| 注釈行・小計行が分離 | テーブル構造の誤認識 | 手動で行を統合。元文書と照合 |
| 表の途中でページが切れる | ページ分割の影響 | 変換後に手動でテーブルを結合 |

---

## 4. OCR 設定（日本語対応）

### 言語設定

```python
# Japanese + English (most common for Japanese business documents)
pipeline_options.ocr_options.lang = ["ja", "en"]

# Japanese only
pipeline_options.ocr_options.lang = ["ja"]
```

### OCR 精度に影響する要因

| 要因 | 影響度 | 推奨値 |
|:---|:---|:---|
| **スキャン解像度** | 最大 | 300 dpi 以上 |
| **文書の傾き** | 高 | 2 度以内（自動補正あり） |
| **フォントサイズ** | 高 | 10pt 以上 |
| **コントラスト** | 中 | 白黒が明瞭 |
| **言語混在** | 中 | 日英混在は `["ja", "en"]` で対応 |
| **手書き** | 高（負の影響） | VLM パイプライン推奨 |

### OCR と VLM の使い分け

| 条件 | 推奨パイプライン | 理由 |
|:---|:---|:---|
| 300dpi+ 印刷物 | Standard OCR | 十分な精度。VLM は過剰 |
| 200dpi 一般スキャン | Standard OCR + 手動補正 | コスパが最適 |
| 低解像度・手書き混在 | VLM (`granite_docling`) | Standard OCR では精度不足 |
| 図表内テキスト重視 | VLM | 図表のコンテキスト認識が優秀 |
| 大量ファイルのバッチ | Standard OCR | VLM は処理速度が遅い |

---

## 5. バッチ処理の設定

### CLI でのバッチ処理

```bash
# Directory batch conversion
docling /path/to/documents/ --to md --output /path/to/output/

# With file type filter
docling /path/to/documents/ --to md --from pdf
```

### Python API でのバッチ処理

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
input_dir = Path("/path/to/documents")

# Collect all supported files
input_files = []
for ext in ["*.pdf", "*.docx", "*.pptx", "*.html"]:
    input_files.extend(input_dir.glob(ext))

# Batch convert
for input_file in input_files:
    try:
        result = converter.convert(str(input_file))
        markdown = result.document.export_to_markdown()
        output_path = input_dir / f"{input_file.stem}.md"
        output_path.write_text(markdown, encoding="utf-8")
        print(f"OK: {input_file.name}")
    except Exception as e:
        print(f"NG: {input_file.name} - {e}")
```

### バッチ処理のパフォーマンス目安

| ファイル種別 | 10 ページ | 50 ページ | 100 ページ |
|:---|:---|:---|:---|
| PDF（テキスト） | 5-10 秒 | 20-40 秒 | 40-80 秒 |
| PDF（OCR） | 30-60 秒 | 2-5 分 | 5-10 分 |
| PDF（VLM） | 2-5 分 | 10-25 分 | 20-50 分 |
| DOCX | 3-5 秒 | 10-20 秒 | 20-40 秒 |
| PPTX | 5-10 秒 | 15-30 秒 | 30-60 秒 |

> 処理時間はマシンスペック（CPU/GPU/メモリ）に大きく依存する。VLM は GPU がある環境で大幅に高速化される。
