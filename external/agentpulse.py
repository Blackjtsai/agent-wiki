# ============================================================
# File: agentpulse.py
# Desc: AgentPULSE (APMS) heartbeat client
# Module: external/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from api.config import settings
from api.database import get_conn, check_db_health

logger = logging.getLogger("atwk.agentpulse")


async def collect_health_detail() -> dict:
    """收集服務健康資訊，供打卡 payload 使用。

    Returns:
        {
            "db":              "ok" | "error",
            "wiki_page_count": int,
            "last_ingest":     "ISO datetime" | None,
            "scheduler":       "running" | "stopped",
        }
    """
    # DB 連線
    db_ok = await check_db_health()

    wiki_page_count = 0
    last_ingest: str | None = None

    if db_ok:
        try:
            async with get_conn() as conn:
                wiki_page_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM atwk_wiki_page WHERE is_delete='N'"
                ) or 0

                last_ingest_ts = await conn.fetchval(
                    "SELECT MAX(ingest_end) FROM atwk_ingest_log WHERE status='S'"
                )
                if last_ingest_ts:
                    last_ingest = last_ingest_ts.isoformat()
        except Exception as e:
            logger.warning(f"health detail 收集失敗：{e}")

    # Scheduler 狀態
    try:
        from job.scheduler import scheduler
        sched_status = "running" if scheduler.running else "stopped"
    except Exception:
        sched_status = "unknown"

    return {
        "db":              "ok" if db_ok else "error",
        "wiki_page_count": wiki_page_count,
        "last_ingest":     last_ingest,
        "scheduler":       sched_status,
    }


async def send_heartbeat(status: str, detail: dict | None = None) -> bool:
    """向 AgentPULSE 發送 Heartbeat 打卡。

    Args:
        status: "ok" | "warning" | "error"
        detail: 健康資訊 dict（None 時自動收集）

    Returns:
        True = 打卡成功，False = 失敗
    """
    if not settings.apms_base_url or not settings.apms_agent_id:
        logger.info("APMS 未設定（APMS_BASE_URL / APMS_AGENT_ID），跳過打卡")
        return False

    if detail is None:
        detail = await collect_health_detail()
        # 若 DB 有問題，自動調整狀態
        if detail.get("db") == "error" and status == "ok":
            status = "warning"

    payload = {
        "agent_code": "ATWK",
        "status":     status,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "detail":     detail,
    }
    url = f"{settings.apms_base_url.rstrip('/')}/agents/{settings.apms_agent_id}/heartbeat"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"AgentPULSE 打卡成功：status={status}, wiki_pages={detail.get('wiki_page_count')}")
            await _write_heartbeat_log(success=True, detail=str(payload))
            return True
    except Exception as e:
        logger.error(f"AgentPULSE 打卡失敗：{e}")
        await _write_heartbeat_log(success=False, detail=str(e))
        return False


async def _write_heartbeat_log(success: bool, detail: str) -> None:
    """寫入 heartbeat JOB 執行記錄至 atwk_job_log。"""
    try:
        async with get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO atwk_job_log
                    (job_name, start_time, end_time, status, result_msg, create_date)
                VALUES ('heartbeat', NOW(), NOW(), $1, $2, NOW())
                """,
                "S" if success else "E",
                detail[:500],
            )
    except Exception:
        pass  # log 失敗不影響主流程
