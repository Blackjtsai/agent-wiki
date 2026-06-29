# ============================================================
# File: lint.py
# Desc: Wiki Lint — format check and wikilink validation
# Module: job/
# Created: 2026-06-28
# Modified: 2026-06-28 (Layer 5 - full implementation)
# Dev: Blackjtsai
# ============================================================

import re
from datetime import datetime, timezone
from pathlib import Path

from api.config import settings
from api.database import get_conn


async def run_lint(page_id: int | None = None) -> dict:
    """執行 Wiki Lint：檢查頁面格式與 wikilinks 有效性。

    檢查項目：
    1. md 檔案是否存在
    2. 頁面是否有 # 標題
    3. wikilinks [[path]] 是否指向存在的頁面
    4. 頁面是否有「## 最後更新」區塊

    Args:
        page_id: 指定頁面 PK（None = 全庫）

    Returns:
        {"success": bool, "pages_checked": int, "issues": list[dict]}
    """
    start_time = datetime.now(timezone.utc)

    # 寫入 JOB log 開始
    async with get_conn() as conn:
        job_log_id = await conn.fetchval(
            """
            INSERT INTO atwk_job_log (job_name, start_time, status, create_date)
            VALUES ('lint', $1, 'R', NOW())
            RETURNING job_log_id
            """,
            start_time,
        )

        # 取得要 Lint 的頁面
        if page_id:
            rows = await conn.fetch(
                "SELECT page_id, page_path, page_title FROM atwk_wiki_page WHERE page_id=$1 AND is_delete='N'",
                page_id,
            )
        else:
            rows = await conn.fetch(
                "SELECT page_id, page_path, page_title FROM atwk_wiki_page WHERE is_delete='N'"
            )

        # 取得所有有效頁面路徑（用於 wikilink 驗證）
        all_paths = set(
            r["page_path"] for r in
            await conn.fetch("SELECT page_path FROM atwk_wiki_page WHERE is_delete='N'")
        )

    wiki_base = Path(settings.wiki_dir)
    issues: list[dict] = []
    pages_checked = 0

    for row in rows:
        page_issues: list[str] = []
        md_path = wiki_base / f"{row['page_path']}.md"
        pages_checked += 1

        # ── 1. 檔案存在性 ────────────────────────────────────
        if not md_path.exists():
            issues.append({
                "page_id":   row["page_id"],
                "page_path": row["page_path"],
                "issue":     "md 檔案不存在",
            })
            continue

        content = md_path.read_text(encoding="utf-8")
        lines   = content.splitlines()

        # ── 2. 標題檢查 ──────────────────────────────────────
        if not any(l.startswith("# ") for l in lines):
            page_issues.append("缺少 H1 標題（應有 # 標題）")

        # ── 3. wikilinks 有效性 ──────────────────────────────
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)
        for link in wikilinks:
            link = link.strip()
            if link not in all_paths:
                page_issues.append(f"wikilink [[{link}]] 指向不存在的頁面")

        # ── 4. 最後更新區塊 ──────────────────────────────────
        if "## 最後更新" not in content:
            page_issues.append("缺少「## 最後更新」區塊")

        # 記錄有問題的頁面
        for iss in page_issues:
            issues.append({
                "page_id":   row["page_id"],
                "page_path": row["page_path"],
                "issue":     iss,
            })

        # 更新 last_lint_date（無論有無問題都更新）
        async with get_conn() as conn:
            await conn.execute(
                "UPDATE atwk_wiki_page SET last_lint_date=NOW(), update_date=NOW() WHERE page_id=$1",
                row["page_id"],
            )

    # 更新 JOB log 完成
    result_msg = f"pages_checked={pages_checked}, issues={len(issues)}"
    async with get_conn() as conn:
        await conn.execute(
            """
            UPDATE atwk_job_log
            SET status='S', end_time=NOW(), result_msg=$1
            WHERE job_log_id=$2
            """,
            result_msg,
            job_log_id,
        )

    return {
        "success":       True,
        "pages_checked": pages_checked,
        "issues":        issues,
    }
