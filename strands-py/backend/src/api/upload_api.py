"""multipart アップロード・成果物一覧・ファイル配信（チャット API とは別ルート）。"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from src.infrastructure.workspace import (
    ARTIFACT_LIST_SUBDIRS,
    PROJECT_SUBDIRS,
    ensure_project_workspace,
)
from src.infrastructure.workspace_catalog import build_workspace_catalog_payload

router = APIRouter(tags=["upload"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

SAFE_NAME = re.compile(
    r"^[^\\/:*?\"<>|]+\.(md|pdf|png|jpe?g|ts|tsx|js|py|ipynb)$", re.IGNORECASE
)


def _validate_project_id(project_id: str) -> None:
    if not project_id or len(project_id) > 128 or not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=422, detail="無効な project_id です")


def _safe_original_name(name: str) -> str:
    base = Path(name).name
    if not base or ".." in base or not SAFE_NAME.match(base):
        raise HTTPException(
            status_code=422,
            detail="ファイル名は .md または .pdf のみ、かつパスを含めないでください",
        )
    return base


def _public_file_url(project_id: str, folder: str, filename: str) -> str:
    return f"/api/files/{project_id}/{folder}/{quote(filename, safe='')}"


def _guess_media_type(filename: str) -> str:
    n = filename.lower()
    if n.endswith(".md"):
        return "text/markdown"
    if n.endswith(".yaml") or n.endswith(".yml"):
        return "text/yaml"
    if n.endswith(".pdf"):
        return "application/pdf"
    if n.endswith(".png"):
        return "image/png"
    if n.endswith(".jpg") or n.endswith(".jpeg"):
        return "image/jpeg"
    if n.endswith(".json"):
        return "application/json"
    if n.endswith(".ipynb"):
        return "application/x-ipynb+json"
    if n.endswith(".ts") or n.endswith(".tsx") or n.endswith(".js") or n.endswith(".py"):
        return "text/plain"
    if n.endswith(".txt") or n.endswith(".csv"):
        return "text/plain"
    return "application/octet-stream"


def _resolved_artifact_path(project_id: str, folder: str, filename: str) -> Path:
    _validate_project_id(project_id)
    if folder not in ARTIFACT_LIST_SUBDIRS:
        raise HTTPException(status_code=422, detail="無効なフォルダです")
    base = Path(filename).name
    if not base or base != filename or ".." in filename:
        raise HTTPException(status_code=422, detail="無効なファイル名です")
    ws = ensure_project_workspace(project_id)
    folder_root = (ws / folder).resolve()
    path = (folder_root / base).resolve()
    try:
        path.relative_to(folder_root)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません") from e
    return path


@router.post("/upload")
async def upload_file(
    project_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    _validate_project_id(project_id)
    raw_name = file.filename or "upload"
    original = _safe_original_name(raw_name)
    suffix = Path(original).suffix.lower()

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="ファイルが大きすぎます（20MB まで）")

    ws = ensure_project_workspace(project_id)
    inbox = ws / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    if suffix == ".md":
        dest_name = original
        dest = inbox / dest_name
        try:
            dest.write_bytes(data)
        except OSError as e:
            raise HTTPException(status_code=502, detail=f"保存に失敗しました: {e}") from e
        return {
            "status": "ok",
            "kind": "markdown",
            "ref": {
                "url": _public_file_url(project_id, "inbox", dest_name),
                "filename": dest_name,
            },
        }

    if suffix == ".pdf":
        stem = Path(original).stem
        dest_name = f"{stem}_{uuid.uuid4().hex[:8]}.pdf"
        dest = inbox / dest_name
        try:
            dest.write_bytes(data)
        except OSError as e:
            raise HTTPException(status_code=502, detail=f"保存に失敗しました: {e}") from e
        return {
            "status": "ok",
            "kind": "pdf",
            "ref": {
                "url": _public_file_url(project_id, "inbox", dest_name),
                "filename": dest_name,
            },
        }

    if suffix in {".png", ".jpg", ".jpeg"}:
        stem = Path(original).stem
        # 元ファイル名はそのまま使わず、衝突しないようにuuidを付与する
        dest_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        dest = inbox / dest_name
        try:
            dest.write_bytes(data)
        except OSError as e:
            raise HTTPException(status_code=502, detail=f"保存に失敗しました: {e}") from e
        return {
            "status": "ok",
            "kind": "image",
            "ref": {
                "url": _public_file_url(project_id, "inbox", dest_name),
                "filename": dest_name,
            },
        }

    if suffix in {".ts", ".tsx", ".js", ".py", ".ipynb"}:
        stem = Path(original).stem
        dest_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        dest = inbox / dest_name
        try:
            dest.write_bytes(data)
        except OSError as e:
            raise HTTPException(status_code=502, detail=f"保存に失敗しました: {e}") from e
        return {
            "status": "ok",
            "kind": "file",
            "ref": {
                "url": _public_file_url(project_id, "inbox", dest_name),
                "filename": dest_name,
            },
        }

    raise HTTPException(
        status_code=422,
        detail="許可されていない拡張子です（.md / .pdf / .png / .jpeg / .ts / .tsx / .js / .py / .ipynb）",
    )


@router.get("/projects/{project_id}/artifacts")
async def list_artifacts(project_id: str) -> dict[str, Any]:
    _validate_project_id(project_id)
    ws = ensure_project_workspace(project_id)
    items: list[dict[str, Any]] = []
    for folder in ARTIFACT_LIST_SUBDIRS:
        d = ws / folder
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if not p.is_file():
                continue
            st = p.stat()
            name = p.name
            modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            items.append(
                {
                    "folder": folder,
                    "filename": name,
                    "url": _public_file_url(project_id, folder, name),
                    "size": st.st_size,
                    "modified": modified.isoformat(),
                }
            )
    items.sort(key=lambda x: x["modified"], reverse=True)
    return {"project_id": project_id, "items": items}


@router.get("/projects/{project_id}/workspace-catalog")
async def get_workspace_catalog(project_id: str) -> dict[str, Any]:
    _validate_project_id(project_id)
    ws = ensure_project_workspace(project_id)
    payload = build_workspace_catalog_payload(ws)
    return {"project_id": project_id, **payload}


@router.get("/files/{project_id}/{folder}/{filename}")
async def serve_project_file(
    project_id: str,
    folder: str,
    filename: str,
    download: bool = Query(False, description="true で Content-Disposition: attachment"),
) -> FileResponse:
    path = _resolved_artifact_path(project_id, folder, filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    base = path.name
    media = _guess_media_type(base)
    disp = "attachment" if download else "inline"
    return FileResponse(
        path,
        media_type=media,
        filename=base,
        content_disposition_type=disp,
    )


@router.delete("/files/{project_id}/{folder}/{filename}")
async def delete_project_file(
    project_id: str,
    folder: str,
    filename: str,
) -> dict[str, bool]:
    path = _resolved_artifact_path(project_id, folder, filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    try:
        path.unlink()
    except OSError as e:
        raise HTTPException(status_code=502, detail=f"削除に失敗しました: {e}") from e
    return {"ok": True}

