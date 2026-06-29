# ============================================================
# File: admin_ingest.py
# Desc: /admin/ingest-logs/* — ingest history, manual trigger
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.database import get_conn
from api.dependencies import require_admin

router = APIRouter(tags=["Admin - Ingest"], dependencies=[Depends(require_admin)])


# ── Schema ───────────────────────────────────────────────────

class IngestLogItem(BaseModel):
    ingest_id: int
    document_id: int
    file_name: str
    ingest_start: datetime
    ingest_end: datetime | None
    status: str
    page_count: int
    error_msg: str | None


class IngestLogListResponse(BaseModel):
    total: int
    items: list[IngestLogItem]


class IngestDetailPage(BaseModel):
    page_id: int
    page_path: str
    page_title: str
    page_category: str


class IngestDetailResponse(BaseModel):
    ingest_id: int
    document_id: int
    file_name: str
    status: str
    page_count: int
    pages: list[IngestDetailPage]


class TriggerResponse(BaseModel):
    success: bool
    message: str
    ingest_id: int | None = None


# ── Routes ───────────────────────────────────────────────────

@router.get("/ingest-logs", response_model=IngestLogListResponse, summary="Ingest 歷程列表")
async def list_ingest_logs(
    limit: int = 50,
    offset: int = 0,
) -> IngestLogListResponse:
    """查詢所有 Ingest 歷程記錄（含文件名稱）。"""
    async with get_conn() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM atwk_ingest_log")
        rows = await conn.fetch(
            """
            SELECT
                l.ingest_id, l.document_id,
                d.file_name,
                l.ingest_start, l.ingest_end,
                l.status, l.page_count, l.error_msg
            FROM atwk_ingest_log l
            JOIN atwk_document d ON d.document_id = l.document_id
            ORDER BY l.ingest_start DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )

    return IngestLogListResponse(
        total=total or 0,
        items=[IngestLogItem(**dict(r)) for r in rows],
    )


@router.post(
    "/ingest-logs/{document_id}/trigger",
    response_model=TriggerResponse,
    summary="手動觸發 Ingest",
)
async def trigger_ingest(
    document_id: int,
    background_tasks: BackgroundTasks,
) -> TriggerResponse:
    """對指定文件觸發 LLM Ingest（背景非同步執行）。

    Args:
        document_id: 要 Ingest 的文件 PK
    """
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT file_path, file_name, ingest_status FROM atwk_document WHERE document_id=$1 AND is_delete='N'",
            document_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="文件不存在")

    if row["ingest_status"] == "R":
        raise HTTPException(status_code=409, detail="Ingest 進行中，請稍後再試")

    # 背景執行
    background_tasks.add_task(
        _run_ingest_task,
        document_id=document_id,
        file_path=row["file_path"],
        file_name=row["file_name"],
    )

    return TriggerResponse(
        success=True,
        message=f"Ingest 已排入背景執行（document_id={document_id}）",
    )


@router.get(
    "/ingest-logs/{ingest_id}/detail",
    response_model=IngestDetailResponse,
    summary="Ingest 明細",
)
async def get_ingest_detail(ingest_id: int) -> IngestDetailResponse:
    """查詢單次 Ingest 產出的 wiki 頁面清單。"""
    async with get_conn() as conn:
        log_row = await conn.fetchrow(
            """
            SELECT l.ingest_id, l.document_id, d.file_name, l.status, l.page_count
            FROM atwk_ingest_log l
            JOIN atwk_document d ON d.document_id = l.document_id
            WHERE l.ingest_id = $1
            """,
            ingest_id,
        )
        if not log_row:
            raise HTTPException(status_code=404, detail="Ingest 記錄不存在")

        pages = await conn.fetch(
            """
            SELECT page_id, page_path, page_title, page_category
            FROM atwk_wiki_page
            WHERE ingest_id = $1 AND is_delete = 'N'
            ORDER BY page_category, page_path
            """,
            ingest_id,
        )

    return IngestDetailResponse(
        **dict(log_row),
        pages=[IngestDetailPage(**dict(p)) for p in pages],
    )


# ── Background task helper ────────────────────────────────────

async def _run_ingest_task(document_id: int, file_path: str, file_name: str) -> None:
    """背景執行 Ingest（供 BackgroundTasks 呼叫）。"""
    from job.ingest import run_ingest
    await run_ingest(document_id=document_id, file_path=file_path, file_name=file_name)
