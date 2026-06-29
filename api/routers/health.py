# ============================================================
# 檔案名稱：health.py
# 中文名稱：健康檢查路由
# 功能說明：GET /health — 回傳服務狀態（含 DB 連線確認）
# 所屬模組：api/routers/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

from fastapi import APIRouter
from api.database import check_db_health

router = APIRouter(tags=["Health"])


@router.get("/health", summary="健康檢查")
async def health_check() -> dict:
    """回傳服務整體健康狀態。

    Returns:
        status: "ok" | "error"
        service: 服務代號 "ATWK"
        db: "ok" | "error"
    """
    db_ok = await check_db_health()

    if db_ok:
        return {
            "status": "ok",
            "service": "ATWK",
            "db": "ok",
        }
    else:
        return {
            "status": "error",
            "service": "ATWK",
            "db": "error",
            "detail": "db connection failed",
        }
