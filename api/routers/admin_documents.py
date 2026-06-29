# ============================================================
# File: admin_documents.py
# Desc: /admin/documents/* — document upload / list / delete
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.config import settings
from api.database import get_conn
from api.dependencies import require_admin
from job.parsers import SUPPORTED_EXTENSIONS

router = APIRouter(tags=["Admin - Documents"], dependencies=[Depends(require_admin)])


# ── Schema ───────────────────────────────────────────────────

class DocumentItem(BaseModel):
    document_id: int
    file_name: str
    file_type: str
    file_size: int
    ingest_status: str
    create_date: datetime


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentItem]


class DeleteResponse(BaseModel):
    success: bool
    message: str


# ── Routes ───────────────────────────────────────────────────

@router.post("/documents/upload", summary="上傳文件至 inbox/")
async def upload_document(file: UploadFile = File(...)) -> dict:
    """將文件儲存至 inbox/ 並在 DB 建立文件索引。

    Args:
        file: 上傳的文件（支援 pptx/docx/pdf/txt/md）

    Returns:
        {"document_id": int, "file_name": str, "message": str}
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的檔案格式：{suffix}（支援：{', '.join(sorted(SUPPORTED_EXTENSIONS))}）",
        )

    # 儲存至 inbox/
    inbox_path = Path(settings.inbox_dir)
    inbox_path.mkdir(parents=True, exist_ok=True)
    dest = inbox_path / (file.filename or "unknown")

    # 若同名檔案已存在，加時間戳避免覆蓋
    if dest.exists():
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = inbox_path / f"{dest.stem}_{ts}{dest.suffix}"

    content = await file.read()
    dest.write_bytes(content)
    file_size = len(content)

    # 寫入 DB
    async with get_conn() as conn:
        doc_id = await conn.fetchval(
            """
            INSERT INTO atwk_document
                (file_name, file_path, file_type, file_size, ingest_status, create_date)
            VALUES ($1, $2, $3, $4, 'P', NOW())
            RETURNING document_id
            """,
            dest.name,
            str(dest),
            suffix.lstrip("."),
            file_size,
        )

    return {
        "document_id": doc_id,
        "file_name": dest.name,
        "message": f"上傳成功，等待 Ingest（document_id={doc_id}）",
    }


@router.get("/documents", response_model=DocumentListResponse, summary="文件列表")
async def list_documents(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> DocumentListResponse:
    """查詢文件列表。

    Args:
        status: 過濾 ingest_status（P/R/D/E），不填則全部
        limit:  每頁筆數（預設 50）
        offset: 偏移量

    Returns:
        DocumentListResponse: 總筆數 + 文件清單
    """
    where = "WHERE is_delete = 'N'"
    params: list = []
    if status:
        params.append(status.upper())
        where += f" AND ingest_status = ${len(params)}"

    async with get_conn() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM atwk_document {where}", *params
        )
        rows = await conn.fetch(
            f"""
            SELECT document_id, file_name, file_type, file_size, ingest_status, create_date
            FROM atwk_document {where}
            ORDER BY create_date DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )

    return DocumentListResponse(
        total=total or 0,
        items=[DocumentItem(**dict(r)) for r in rows],
    )


@router.delete("/documents/{document_id}", response_model=DeleteResponse, summary="刪除文件")
async def delete_document(document_id: int) -> DeleteResponse:
    """軟刪除文件（is_delete='Y'），並嘗試移除 inbox/ 中的實體檔案。

    只能刪除 ingest_status='P'（尚未 Ingest）的文件。
    """
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT file_path, ingest_status FROM atwk_document WHERE document_id=$1 AND is_delete='N'",
            document_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="文件不存在")

        if row["ingest_status"] not in ("P", "E"):
            raise HTTPException(
                status_code=400,
                detail=f"只能刪除待 Ingest 或失敗的文件（目前狀態：{row['ingest_status']}）",
            )

        await conn.execute(
            "UPDATE atwk_document SET is_delete='Y', update_date=NOW() WHERE document_id=$1",
            document_id,
        )

    # 嘗試移除實體檔案（inbox/）
    file_path = Path(row["file_path"])
    if file_path.exists() and str(settings.inbox_dir) in str(file_path):
        try:
            file_path.unlink()
        except OSError:
            pass  # 實體刪除失敗不影響 DB 記錄

    return DeleteResponse(success=True, message=f"document_id={document_id} 已刪除")
