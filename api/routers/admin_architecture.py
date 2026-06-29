# ============================================================
# 檔案名稱：admin_architecture.py
# 中文名稱：系統架構文件 API
# 功能說明：提供後台讀取 docs/design/ARCHITECTURE.md 內容
# 所屬模組：api/routers/
# 建立日期：2026-06-30
# 修改日期：2026-06-30
# 開發者　：Blackjtsai
# ============================================================

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import require_admin

router = APIRouter(tags=["Admin - Architecture"], dependencies=[Depends(require_admin)])

ROOT = Path(__file__).parent.parent.parent
ARCHITECTURE_PATH = ROOT / "docs" / "design" / "ARCHITECTURE.md"


class ArchitectureResponse(BaseModel):
    content: str


@router.get("/architecture", response_model=ArchitectureResponse, summary="讀取系統架構文件")
async def get_architecture() -> ArchitectureResponse:
    """讀取 docs/design/ARCHITECTURE.md 原始內容供後台渲染。"""
    if not ARCHITECTURE_PATH.exists():
        raise HTTPException(status_code=404, detail="ARCHITECTURE.md 不存在")
    return ArchitectureResponse(content=ARCHITECTURE_PATH.read_text(encoding="utf-8"))
