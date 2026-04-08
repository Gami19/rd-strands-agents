"""Compatibility tools for KC skills on Strands."""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from strands import tool

SUPPORTED_DOC_EXTS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _normalize_drawio_name(filename: str) -> str:
    base = Path(filename).name.strip()
    if not base:
        base = "diagram.drawio"
    if not base.endswith(".drawio"):
        base = f"{Path(base).stem}.drawio"
    return base


def _drawio_tool_return_xml(xml: str) -> str:
    text = xml.lstrip("\ufeff").strip()
    return f"```xml\n{text}\n```"


def _make_drawio_xml(diagram_title: str, body: str) -> str:
    safe_title = html.escape(diagram_title)
    safe_body = html.escape(body).replace("\n", "&#xa;")
    return (
        "<mxfile host=\"app.diagrams.net\" modified=\"{modified}\" agent=\"strands\" version=\"24.7.7\">\n"
        "  <diagram id=\"diagram-1\" name=\"Page-1\">\n"
        "    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" "
        "arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\"1169\" pageHeight=\"827\" math=\"0\" shadow=\"0\">\n"
        "      <root>\n"
        "        <mxCell id=\"0\"/>\n"
        "        <mxCell id=\"1\" parent=\"0\"/>\n"
        "        <mxCell id=\"title\" value=\"{title}\" style=\"text;html=1;strokeColor=none;fillColor=none;align=left;"
        "verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1;\" vertex=\"1\" parent=\"1\">\n"
        "          <mxGeometry x=\"40\" y=\"24\" width=\"800\" height=\"32\" as=\"geometry\"/>\n"
        "        </mxCell>\n"
        "        <mxCell id=\"content\" value=\"{content}\" style=\"rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;"
        "strokeColor=#666666;align=left;verticalAlign=top;spacing=10;\" vertex=\"1\" parent=\"1\">\n"
        "          <mxGeometry x=\"40\" y=\"72\" width=\"1080\" height=\"680\" as=\"geometry\"/>\n"
        "        </mxCell>\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    ).format(
        modified=_utc_now_iso(),
        title=safe_title,
        content=safe_body,
    )


def _strip_html_to_text(raw_html: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", raw_html)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _resolve_input_path(workspace_root: Path, input_path: str) -> Path:
    p = Path(input_path)
    if p.is_absolute():
        resolved = p.resolve()
    else:
        inbox_candidate = (workspace_root / "inbox" / p).resolve()
        if inbox_candidate.exists():
            resolved = inbox_candidate
        else:
            resolved = (workspace_root / p).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")
    if resolved.suffix.lower() not in SUPPORTED_DOC_EXTS:
        raise ValueError(f"未対応の拡張子です: {resolved.suffix}")
    return resolved


def build_compat_tools(workspace_root: Path) -> list[Any]:
    ws = workspace_root.resolve()
    inbox = (ws / "inbox").resolve()
    proposal = (ws / "proposal").resolve()
    inbox.mkdir(parents=True, exist_ok=True)
    proposal.mkdir(parents=True, exist_ok=True)

    @tool
    def pdf_convert_to_inbox(
        input_path: str, output_filename: str = "", ocr: bool = False
    ) -> str:
        """
        PDF/DOCX/PPTX 等を Markdown に変換して inbox へ保存する。
        input_path は絶対パス、または workspace/inbox 相対パスで指定可能。
        """
        try:
            src = _resolve_input_path(ws, input_path)
            if output_filename.strip():
                out_name = Path(output_filename).name
            else:
                out_name = f"{src.stem}.md"
            out = (inbox / out_name).resolve()
            try:
                out.relative_to(inbox)
            except ValueError as e:
                raise ValueError("出力先は inbox 配下のみ指定可能です") from e

            # OCR フラグは互換のため受け付ける。Docling 側設定は今後拡張。
            _ = ocr
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(str(src))
            markdown = result.document.export_to_markdown()
            frontmatter = (
                "---\n"
                f"source: \"{src.name}\"\n"
                f"converted_at: \"{_utc_now_iso()}\"\n"
                "converter: \"docling\"\n"
                "---\n\n"
            )
            out.write_text(frontmatter + markdown, encoding="utf-8")
            return _as_json(
                {
                    "status": "ok",
                    "tool": "pdf_convert_to_inbox",
                    "input": str(src),
                    "output": str(out),
                }
            )
        except ModuleNotFoundError:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "pdf_convert_to_inbox",
                    "reason": "docling が未インストールのため変換を実行できませんでした。",
                    "next_actions": [
                        "backend 環境に docling をインストールしてください。",
                        "インストール後に同じ入力で再実行してください。",
                    ],
                }
            )
        except Exception as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "pdf_convert_to_inbox",
                    "reason": str(e),
                    "next_actions": [
                        "入力ファイルの存在と拡張子を確認してください。",
                        "必要に応じて出力ファイル名を明示してください。",
                    ],
                }
            )

    @tool
    def diagram_generate_drawio(
        diagram_brief: str,
        output_filename: str = "architecture.drawio",
        title: str = "Architecture Diagram",
    ) -> str:
        """
        図の要件テキストから draw.io 互換 XML ファイルを proposal 配下に保存する。
        成功時の戻り値は説明文なしで、<mxfile> から始まる XML のみを ```xml コードブロックで返す。
        """
        try:
            out_name = _normalize_drawio_name(output_filename)
            out = (proposal / out_name).resolve()
            try:
                out.relative_to(proposal)
            except ValueError as e:
                raise ValueError("出力先は proposal 配下のみ指定可能です") from e

            xml = _make_drawio_xml(diagram_title=title, body=diagram_brief)
            out.write_text(xml, encoding="utf-8")
            return _drawio_tool_return_xml(xml)
        except Exception as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "diagram_generate_drawio",
                    "reason": str(e),
                    "next_actions": [
                        "図に含める要素を箇条書きで明示してください。",
                        "output_filename を .drawio で指定してください。",
                    ],
                }
            )

    @tool
    def web_fetch_text(url: str, max_chars: int = 8000) -> str:
        """
        外部 URL からテキストを取得して返す。HTML はプレーンテキスト化する。
        """
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("URL は http/https の完全な形式で指定してください。")
            req = Request(
                url,
                headers={"User-Agent": "strands-skills-compat/1.0"},
            )
            with urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()

            text = raw.decode("utf-8", errors="replace")
            if "html" in content_type.lower():
                text = _strip_html_to_text(text)
            text = text[: max(200, min(max_chars, 20000))]
            return _as_json(
                {
                    "status": "ok",
                    "tool": "web_fetch_text",
                    "url": url,
                    "content": text,
                }
            )
        except (HTTPError, URLError, TimeoutError) as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "web_fetch_text",
                    "reason": f"取得に失敗しました: {e}",
                    "next_actions": ["URL の有効性とアクセス可能性を確認してください。"],
                }
            )
        except Exception as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "web_fetch_text",
                    "reason": str(e),
                    "next_actions": ["URL を http/https の形式で再指定してください。"],
                }
            )

    @tool
    def brave_web_search(query: str, count: int = 8) -> str:
        """
        Brave Search API で Web 検索する。検索語は自然言語でよい。
        サーバーに BRAVE_API_KEY（環境変数）が必要。
        """
        api_key = (os.getenv("BRAVE_API_KEY") or "").strip()
        if not api_key:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "brave_web_search",
                    "reason": "BRAVE_API_KEY が設定されていません。",
                    "next_actions": [
                        "strands-py/backend/.env に BRAVE_API_KEY を設定し、バックエンドを再起動してください。",
                    ],
                }
            )

        q = (query or "").strip()
        if not q:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "brave_web_search",
                    "reason": "query が空です。",
                    "next_actions": ["検索語を指定してください。"],
                }
            )

        try:
            n = int(count)
        except (TypeError, ValueError):
            n = 8
        n = max(1, min(n, 20))

        url = (
            "https://api.search.brave.com/res/v1/web/search?"
            + urlencode({"q": q, "count": str(n)})
        )
        req = Request(
            url,
            headers={
                "X-Subscription-Token": api_key,
                "Accept": "application/json",
                "User-Agent": "strands-skills-compat/1.0",
            },
        )
        try:
            with urlopen(req, timeout=20) as resp:
                raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "brave_web_search",
                    "reason": f"Brave API の呼び出しに失敗しました: {e}",
                    "next_actions": [
                        "API キーとネットワークを確認してください。",
                        "検索語を短くして再試行してください。",
                    ],
                }
            )
        except Exception as e:
            return _as_json(
                {
                    "status": "partial_success",
                    "tool": "brave_web_search",
                    "reason": str(e),
                    "next_actions": ["しばらくしてから再試行してください。"],
                }
            )

        web = data.get("web") if isinstance(data, dict) else None
        results = (web or {}).get("results") if isinstance(web, dict) else None
        if not isinstance(results, list):
            results = []

        snippets: list[str] = []
        for i, item in enumerate(results[:n], 1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            page_url = str(item.get("url") or "").strip()
            desc = str(item.get("description") or "").strip()
            line = f"{i}. {title}\n   {page_url}\n   {desc}"
            snippets.append(line)

        query_meta = ""
        if isinstance(data, dict):
            qobj = data.get("query")
            if isinstance(qobj, dict) and qobj.get("original"):
                query_meta = str(qobj.get("original"))

        return _as_json(
            {
                "status": "ok",
                "tool": "brave_web_search",
                "query": query_meta or q,
                "results": snippets,
                "raw_result_count": len(results),
            }
        )

    return [
        pdf_convert_to_inbox,
        diagram_generate_drawio,
        web_fetch_text,
        brave_web_search,
    ]

