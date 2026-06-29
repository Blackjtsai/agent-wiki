# ============================================================
# File: admin_wiki.py
# Desc: /admin/wiki-pages/* — wiki page list / view / delete / lint
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.config import settings
from api.database import get_conn
from api.dependencies import require_admin

router = APIRouter(tags=["Admin - Wiki"], dependencies=[Depends(require_admin)])


# ── Schema ───────────────────────────────────────────────────

class WikiPageItem(BaseModel):
    page_id: int
    page_path: str
    page_title: str
    page_category: str
    last_lint_date: datetime | None
    create_date: datetime


class WikiPageListResponse(BaseModel):
    total: int
    items: list[WikiPageItem]


class WikiPageContent(BaseModel):
    page_id: int
    page_path: str
    page_title: str
    page_category: str
    content: str
    last_lint_date: datetime | None


class DeleteResponse(BaseModel):
    success: bool
    message: str


class LintResponse(BaseModel):
    success: bool
    message: str
    pages_linted: int


# ── Routes ───────────────────────────────────────────────────

@router.get("/wiki-pages", response_model=WikiPageListResponse, summary="Wiki 頁面列表")
async def list_wiki_pages(
    category: str | None = None,
    keyword: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> WikiPageListResponse:
    """查詢 Wiki 頁面清單（可按 category 或關鍵字過濾）。"""
    conditions = ["is_delete = 'N'"]
    params: list = []

    if category:
        params.append(category)
        conditions.append(f"page_category = ${len(params)}")

    if keyword:
        params.append(f"%{keyword}%")
        conditions.append(f"(page_title ILIKE ${len(params)} OR page_path ILIKE ${len(params)})")

    where = "WHERE " + " AND ".join(conditions)

    async with get_conn() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM atwk_wiki_page {where}", *params
        )
        rows = await conn.fetch(
            f"""
            SELECT page_id, page_path, page_title, page_category, last_lint_date, create_date
            FROM atwk_wiki_page {where}
            ORDER BY page_category, page_path
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )

    return WikiPageListResponse(
        total=total or 0,
        items=[WikiPageItem(**dict(r)) for r in rows],
    )


@router.get("/wiki-pages/{page_id}", response_model=WikiPageContent, summary="Wiki 頁面內容")
async def get_wiki_page(page_id: int) -> WikiPageContent:
    """讀取指定 wiki 頁面的 Markdown 內容。"""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT page_id, page_path, page_title, page_category, last_lint_date
            FROM atwk_wiki_page
            WHERE page_id = $1 AND is_delete = 'N'
            """,
            page_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Wiki 頁面不存在")

    md_path = Path(settings.wiki_dir) / f"{row['page_path']}.md"
    if not md_path.exists():
        content = "（檔案不存在，可能已被手動刪除）"
    else:
        content = md_path.read_text(encoding="utf-8")

    return WikiPageContent(**dict(row), content=content)


@router.delete("/wiki-pages/{page_id}", response_model=DeleteResponse, summary="刪除 Wiki 頁面")
async def delete_wiki_page(page_id: int) -> DeleteResponse:
    """軟刪除 Wiki 頁面（is_delete='Y'）並移除對應 md 檔案。"""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT page_path FROM atwk_wiki_page WHERE page_id=$1 AND is_delete='N'",
            page_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Wiki 頁面不存在")

        await conn.execute(
            "UPDATE atwk_wiki_page SET is_delete='Y', update_date=NOW() WHERE page_id=$1",
            page_id,
        )

    # 移除 md 檔案
    md_path = Path(settings.wiki_dir) / f"{row['page_path']}.md"
    if md_path.exists():
        try:
            md_path.unlink()
        except OSError:
            pass

    return DeleteResponse(success=True, message=f"page_id={page_id} 已刪除")


@router.post("/wiki-pages/lint", response_model=LintResponse, summary="執行 Wiki Lint")
async def trigger_lint(
    page_id: int | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> LintResponse:
    """觸發 Wiki Lint：檢查並修正 wiki 頁面格式、wikilinks 有效性。

    Args:
        page_id: 指定頁面 PK（不填則對全庫執行）
    """
    if page_id:
        async with get_conn() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM atwk_wiki_page WHERE page_id=$1 AND is_delete='N'",
                page_id,
            )
        if not exists:
            raise HTTPException(status_code=404, detail="Wiki 頁面不存在")
        background_tasks.add_task(_run_lint_task, page_id=page_id)
        return LintResponse(success=True, message=f"Lint 已排入背景（page_id={page_id}）", pages_linted=1)
    else:
        background_tasks.add_task(_run_lint_task, page_id=None)
        return LintResponse(success=True, message="全庫 Lint 已排入背景執行", pages_linted=0)


# ── Background task helper ────────────────────────────────────

async def _run_lint_task(page_id: int | None) -> None:
    """背景執行 Lint（供 BackgroundTasks 呼叫）。Layer 5 實作完整邏輯。"""
    from job.lint import run_lint
    await run_lint(page_id=page_id)
