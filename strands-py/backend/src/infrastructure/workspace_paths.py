"""workspace の area / relative_path 正規化（file_read / file_write / workspace_list で共有）。"""

from __future__ import annotations

from pathlib import Path

WORKSPACE_AREAS = frozenset({"inbox", "notes", "proposal", "decision", "agents"})


def normalize_area(raw: str) -> str:
    a = (raw or "").strip().lower()
    if a not in WORKSPACE_AREAS:
        raise ValueError(
            "area は inbox, notes, proposal, decision, agents のいずれかを指定してください"
            f"（指定値: {raw!r}）"
        )
    return a


def normalize_workspace_relative_filename(relative_path: str) -> str:
    """
    area 直下のファイル名 1 つのみ許可（サブディレクトリ・.. 不可）。
    戻り値は正規化済みのファイル名。
    """
    rel = (relative_path or "").strip()
    if not rel:
        raise ValueError("relative_path は必須です")

    normalized = rel.replace("\\", "/").strip()
    normalized = normalized.removeprefix("./")
    while normalized.startswith("/"):
        normalized = normalized[1:]

    if not normalized:
        raise ValueError("relative_path はファイル名 1 つを指定してください（サブディレクトリ不可）")

    parts = Path(normalized).parts
    if len(parts) != 1:
        raise ValueError(
            "relative_path はパス区切りを含めない 1 ファイル名のみ指定してください"
        )
    name = parts[0]
    if name in (".", ".."):
        raise ValueError("relative_path に . や .. は使えません")
    if Path(normalized).is_absolute():
        raise ValueError("relative_path は相対のファイル名のみ指定してください")
    return name


def resolve_workspace_area_path(
    ws: Path,
    area: str,
    relative_path: str,
    *,
    action: str,
) -> Path:
    """許可領域と単一ファイル名から絶対パスを求める。"""
    a = normalize_area(area)
    name = normalize_workspace_relative_filename(relative_path)
    base = (ws / a).resolve()
    candidate = (base / name).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise ValueError(f"{action}: 領域 {a} 配下のみアクセス可能です") from e
    return candidate
