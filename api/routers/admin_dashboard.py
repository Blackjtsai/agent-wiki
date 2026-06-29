# ============================================================
# 檔案名稱：admin_dashboard.py
# 中文名稱：後台儀表板 API
# 功能說明：彙整系統運作狀態、資料統計、磁碟使用量
# 所屬模組：api/routers/
# 建立日期：2026-06-29
# 修改日期：2026-06-29
# 開發者　：Blackjtsai
# ============================================================

import os
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.config import settings
from api.database import get_conn
from api.dependencies import require_admin

router = APIRouter(tags=["Admin - Dashboard"], dependencies=[Depends(require_admin)])

ROOT = Path(__file__).parent.parent.parent


def _dir_size_mb(path: Path) -> float:
    """計算目錄總大小（MB）。"""
    total = 0
    if path.exists():
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return round(total / 1024 / 1024, 2)


def _dir_file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for f in path.rglob("*") if f.is_file())


class ServiceStatus(BaseModel):
    name: str
    status: str      # ok / warn / error
    detail: str


class DiskUsage(BaseModel):
    path: str
    size_mb: float
    files: int


class RecentIngest(BaseModel):
    ingest_id: int
    file_name: str
    status: str
    page_count: int
    ingest_start: str


class DashboardResponse(BaseModel):
    services: list[ServiceStatus]
    stats: dict
    disk: list[DiskUsage]
    scheduler: dict
    recent_ingest: list[RecentIngest]


@router.get("/dashboard", response_model=DashboardResponse, summary="儀表板彙整資料")
async def dashboard() -> DashboardResponse:
    """回傳儀表板所需的所有系統資料。"""

    async with get_conn() as conn:
        # ── 資料統計 ────────────────────────────────────────────
        doc_total   = await conn.fetchval("SELECT COUNT(*) FROM atwk_document WHERE is_delete='N'") or 0
        doc_pending = await conn.fetchval("SELECT COUNT(*) FROM atwk_document WHERE ingest_status='P' AND is_delete='N'") or 0
        doc_done    = await conn.fetchval("SELECT COUNT(*) FROM atwk_document WHERE ingest_status='D' AND is_delete='N'") or 0
        doc_error   = await conn.fetchval("SELECT COUNT(*) FROM atwk_document WHERE ingest_status='E' AND is_delete='N'") or 0
        wiki_total  = await conn.fetchval("SELECT COUNT(*) FROM atwk_wiki_page WHERE is_delete='N'") or 0
        ingest_total= await conn.fetchval("SELECT COUNT(*) FROM atwk_ingest_log") or 0
        job_total   = await conn.fetchval("SELECT COUNT(*) FROM atwk_job_log") or 0
        job_ok      = await conn.fetchval("SELECT COUNT(*) FROM atwk_job_log WHERE status='success'") or 0
        job_fail    = await conn.fetchval("SELECT COUNT(*) FROM atwk_job_log WHERE status='error'") or 0

        # ── 最近 Ingest ──────────────────────────────────────────
        rows = await conn.fetch("""
            SELECT l.ingest_id, d.file_name, l.status, l.page_count, l.ingest_start
            FROM atwk_ingest_log l
            JOIN atwk_document d ON d.document_id = l.document_id
            ORDER BY l.ingest_start DESC LIMIT 5
        """)
        recent_ingest = [
            RecentIngest(
                ingest_id=r["ingest_id"],
                file_name=r["file_name"],
                status=r["status"],
                page_count=r["page_count"] or 0,
                ingest_start=str(r["ingest_start"]),
            ) for r in rows
        ]

    # ── 服務狀態 ─────────────────────────────────────────────
    services = [
        ServiceStatus(name="FastAPI", status="ok", detail="Port 8300 運行中"),
        ServiceStatus(name="PostgreSQL", status="ok", detail=f"db_atwk 連線正常"),
        ServiceStatus(
            name="LLM",
            status="ok" if settings.llm_api_key else "warn",
            detail=f"{settings.llm_model}" if settings.llm_api_key else "API Key 未設定",
        ),
    ]

    # APScheduler
    try:
        from job.scheduler import scheduler
        running = scheduler.running
        job_count = len(scheduler.get_jobs())
        services.append(ServiceStatus(
            name="APScheduler",
            status="ok" if running else "error",
            detail=f"{'運行中' if running else '已停止'}，{job_count} 個 JOB",
        ))

        sched_jobs = [
            {
                "id": j.id,
                "name": j.name,
                "next_run": str(j.next_run_time) if j.next_run_time else "paused",
            }
            for j in scheduler.get_jobs()
        ]
        scheduler_info = {"running": running, "jobs": sched_jobs}
    except Exception as e:
        services.append(ServiceStatus(name="APScheduler", status="error", detail=str(e)))
        scheduler_info = {"running": False, "jobs": []}

    # APMS
    services.append(ServiceStatus(
        name="AgentPULSE",
        status="ok" if settings.apms_base_url else "warn",
        detail=settings.apms_base_url or "未設定 APMS_BASE_URL",
    ))

    # ── 磁碟使用 ─────────────────────────────────────────────
    disk = [
        DiskUsage(path="wiki/",      size_mb=_dir_size_mb(ROOT / "wiki"),      files=_dir_file_count(ROOT / "wiki")),
        DiskUsage(path="raw/",       size_mb=_dir_size_mb(ROOT / "raw"),        files=_dir_file_count(ROOT / "raw")),
        DiskUsage(path="inbox/",     size_mb=_dir_size_mb(ROOT / "inbox"),      files=_dir_file_count(ROOT / "inbox")),
        DiskUsage(path="templates/", size_mb=_dir_size_mb(ROOT / "templates"),  files=_dir_file_count(ROOT / "templates")),
    ]

    return DashboardResponse(
        services=services,
        stats={
            "documents": {"total": doc_total, "pending": doc_pending, "done": doc_done, "error": doc_error},
            "wiki_pages": wiki_total,
            "ingest_logs": ingest_total,
            "job_logs": {"total": job_total, "success": job_ok, "error": job_fail},
        },
        disk=disk,
        scheduler=scheduler_info,
        recent_ingest=recent_ingest,
    )
