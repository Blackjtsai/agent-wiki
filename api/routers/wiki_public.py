# ============================================================
# File: wiki_public.py
# Desc: /api/wiki-pages/* — public wiki browse endpoints (no auth)
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.config import settings
from api.database import get_conn

router = APIRouter(tags=["Wiki - Public"])


# ── Schema ───────────────────────────────────────────────────

class WikiPageSummary(BaseModel):
    page_id: int
    page_path: str
    page_title: str
    page_category: str


class WikiPagesByCategory(BaseModel):
    """前台目錄樹結構：按 category 分群。"""
    concepts:     list[WikiPageSummary]
    operations:   list[WikiPageSummary]
    architecture: list[WikiPageSummary]
    sources:      list[WikiPageSummary]
    syntheses:    list[WikiPageSummary]
    total: int


class WikiPageDetail(BaseModel):
    page_id: int
    page_path: str
    page_title: str
    page_category: str
    content: str


# ── Routes ───────────────────────────────────────────────────

@router.get("/wiki-pages", response_model=WikiPagesByCategory, summary="Wiki 目錄（公開）")
async def list_wiki_pages_public() -> WikiPagesByCategory:
    """回傳所有 wiki 頁面，按 category 分群，供前台目錄樹使用。"""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT page_id, page_path, page_title, page_category
            FROM atwk_wiki_page
            WHERE is_delete = 'N'
            ORDER BY page_category, page_title
            """
        )

    grouped: dict[str, list[WikiPageSummary]] = {
        "concepts": [], "operations": [], "architecture": [],
        "sources": [], "syntheses": [],
    }

    for r in rows:
        item = WikiPageSummary(**dict(r))
        cat = r["page_category"]
        if cat in grouped:
            grouped[cat].append(item)
        else:
            grouped.setdefault(cat, []).append(item)

    return WikiPagesByCategory(**grouped, total=len(rows))


@router.get("/wiki-pages/{page_id}", response_model=WikiPageDetail, summary="Wiki 頁面內容（公開）")
async def get_wiki_page_public(page_id: int) -> WikiPageDetail:
    """回傳指定 wiki 頁面的 Markdown 內容（公開，無需 Token）。"""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT page_id, page_path, page_title, page_category
            FROM atwk_wiki_page
            WHERE page_id = $1 AND is_delete = 'N'
            """,
            page_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Wiki 頁面不存在")

    md_path = Path(settings.wiki_dir) / f"{row['page_path']}.md"
    content = md_path.read_text(encoding="utf-8") if md_path.exists() else "（內容不存在）"

    return WikiPageDetail(**dict(row), content=content)
