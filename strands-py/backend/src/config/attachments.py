from __future__ import annotations


def format_attachments_instruction(*, base_message: str, attachments_block: str) -> str:
    return (
        "添付ファイルがあります。以下はプロジェクトの `inbox/` に保存済みで、"
        "参照するときは `file_read(area=\"inbox\", relative_path=<filename>)` の形式で指定してください"
        "（relative_path には下記のファイル名をそのまま使う。.. は不可）。\n\n"
        f"{attachments_block}\n\n"
        "また `pdf_convert_to_inbox` の入力 `input_path` は、上記の `filename` を"
        "相対パスとして指定すれば `inbox/` 配下が解決されます（絶対パス指定でも可）。\n\n"
        f"ユーザー依頼: {base_message}"
    )

