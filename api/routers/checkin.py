# ============================================================
# File: checkin.py
# Desc: GET /api/checkin — service health check-in endpoint
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Check-in"])


class CheckinResponse(BaseModel):
    agent:     str
    status:    str
    timestamp: str
    detail:    dict


@router.get("/checkin", response_model=CheckinResponse, summary="服務健康打卡")
async def checkin() -> CheckinResponse:
    """回傳 ATWK 服務健康狀態，並同步向 AgentPULSE 發送一次 Heartbeat。

    供外部（AgentHQ）呼叫確認服務就緒，也可作為手動觸發打卡的入口。

    Returns:
        CheckinResponse: agent 代號、狀態、時間戳、健康明細
    """
    from external.agentpulse import collect_health_detail, send_heartbeat

    detail = await collect_health_detail()

    # 決定整體狀態
    if detail.get("db") == "error":
        status = "error"
    elif detail.get("scheduler") == "stopped":
        status = "warning"
    else:
        status = "ok"

    # 非同步打卡（不等待結果，避免阻塞回應）
    import asyncio
    asyncio.create_task(send_heartbeat(status=status, detail=detail))

    return CheckinResponse(
        agent="ATWK",
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detail=detail,
    )
