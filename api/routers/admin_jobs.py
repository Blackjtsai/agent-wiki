# ============================================================
# File: admin_jobs.py
# Desc: /admin/job-logs — JOB execution history query
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.database import get_conn
from api.dependencies import require_admin

router = APIRouter(tags=["Admin - Jobs"], dependencies=[Depends(require_admin)])


# ── Schema ───────────────────────────────────────────────────

class JobLogItem(BaseModel):
    job_log_id: int
    job_name:   str
    start_time: datetime
    end_time:   datetime | None
    status:     str
    result_msg: str | None


class JobLogListResponse(BaseModel):
    total: int
    items: list[JobLogItem]


# ── Routes ───────────────────────────────────────────────────

@router.get("/job-logs", response_model=JobLogListResponse, summary="JOB 執行記錄")
async def list_job_logs(
    job_name: str | None = None,
    limit:    int = 50,
    offset:   int = 0,
) -> JobLogListResponse:
    """查詢 JOB 執行記錄，可按 job_name 過濾。

    Args:
        job_name: inbox_scan / ingest / lint / heartbeat（不填則全部）
        limit:    每頁筆數
        offset:   偏移量
    """
    conditions = ["1=1"]
    params: list = []

    if job_name:
        params.append(job_name)
        conditions.append(f"job_name = ${len(params)}")

    where = "WHERE " + " AND ".join(conditions)

    async with get_conn() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM atwk_job_log {where}", *params
        )
        rows = await conn.fetch(
            f"""
            SELECT job_log_id, job_name, start_time, end_time, status, result_msg
            FROM atwk_job_log {where}
            ORDER BY start_time DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )

    return JobLogListResponse(
        total=total or 0,
        items=[JobLogItem(**dict(r)) for r in rows],
    )


@router.get("/scheduler/status", summary="排程器狀態")
async def scheduler_status() -> dict:
    """回傳 APScheduler 目前的 JOB 清單與下次執行時間。"""
    from job.scheduler import scheduler

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id":            job.id,
            "name":          job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else "paused",
        })

    return {
        "running": scheduler.running,
        "jobs":    jobs,
    }
