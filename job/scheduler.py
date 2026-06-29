# ============================================================
# File: scheduler.py
# Desc: APScheduler initialization and job registration
# Module: job/
# Created: 2026-06-28
# Modified: 2026-06-28 (Layer 6 - heartbeat enabled)
# Dev: Blackjtsai
# ============================================================

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("atwk.scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


def setup_scheduler() -> AsyncIOScheduler:
    """Register all JOBs and return scheduler (not yet started).

    JOBs:
    - inbox_scan : every 5 min
    - daily_lint : daily at 02:00
    - heartbeat  : every 10 min (AgentPULSE)
    """
    scheduler.add_job(
        _job_inbox_scan,
        trigger=IntervalTrigger(minutes=5),
        id="inbox_scan",
        name="inbox auto scan",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    scheduler.add_job(
        _job_daily_lint,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_lint",
        name="daily wiki lint",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        _job_heartbeat,
        trigger=IntervalTrigger(minutes=10),
        id="heartbeat",
        name="AgentPULSE Heartbeat",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    logger.info("APScheduler JOBs registered: inbox_scan, daily_lint, heartbeat")
    return scheduler


async def _job_inbox_scan() -> None:
    try:
        from job.inbox_scan import run_inbox_scan
        result = await run_inbox_scan()
        logger.info(f"[inbox_scan] {result}")
    except Exception as e:
        logger.error(f"[inbox_scan] failed: {e}", exc_info=True)
        await _write_job_error("inbox_scan", str(e))


async def _job_daily_lint() -> None:
    try:
        from job.lint import run_lint
        result = await run_lint(page_id=None)
        logger.info(f"[daily_lint] pages_checked={result['pages_checked']}, issues={len(result['issues'])}")
    except Exception as e:
        logger.error(f"[daily_lint] failed: {e}", exc_info=True)
        await _write_job_error("daily_lint", str(e))


async def _job_heartbeat() -> None:
    try:
        from external.agentpulse import send_heartbeat
        ok = await send_heartbeat(status="ok", detail=None)
        logger.info(f"[heartbeat] {'success' if ok else 'skipped/failed'}")
    except Exception as e:
        logger.error(f"[heartbeat] failed: {e}", exc_info=True)
        await _write_job_error("heartbeat", str(e))


async def _write_job_error(job_name: str, error_msg: str) -> None:
    try:
        from api.database import get_conn
        async with get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO atwk_job_log (job_name, start_time, end_time, status, result_msg, create_date)
                VALUES ($1, NOW(), NOW(), 'E', $2, NOW())
                """,
                job_name,
                error_msg[:500],
            )
    except Exception:
        pass
