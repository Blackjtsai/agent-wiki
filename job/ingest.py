# ============================================================
# 檔案名稱：ingest.py
# 中文名稱：LLM Ingest 核心邏輯
# 功能說明：將原始文件透過 LLM 分析，產出 wiki 頁面並寫入 DB
# 所屬模組：job/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from api.config import settings
from api.database import get_conn
from api.llm import chat
from job.parsers import extract_text


# ── Prompt 定義 ──────────────────────────────────────────────

INGEST_SYSTEM_PROMPT = """你是一個知識庫管理 AI。
你的任務是分析使用者提供的文件，將其拆解為結構化的 Wiki 知識頁面。

## 輸出規則

1. 每個 Wiki 頁面聚焦一個主題，不要把所有內容塞進一頁
2. 頁面分類（category）只能是以下五種之一：
   - concepts（概念說明、功能描述、業務邏輯）
   - operations（操作流程、JOB、排程、監控）
   - architecture（系統架構、環境、部署）
   - sources（來源文件摘要，一份文件一頁）
   - syntheses（跨文件綜合分析，通常不在此階段產生）
3. page_path 格式：{category}/{slug}（slug 用英文小寫加底線，不含副檔名）
4. 內容使用繁體中文
5. 使用 [[page_path]] 格式建立跨頁連結（wikilinks）
6. 每頁結尾加「## 最後更新\nYYYY-MM-DD」

## 輸出格式（嚴格 JSON）

```json
{
  "source_summary": "一段話說明此文件的主題和重要性",
  "pages": [
    {
      "page_path": "sources/document_name",
      "page_title": "文件標題",
      "category": "sources",
      "content": "完整 Markdown 內容"
    },
    {
      "page_path": "concepts/topic_name",
      "page_title": "主題名稱",
      "category": "concepts",
      "content": "完整 Markdown 內容"
    }
  ]
}
```

只輸出 JSON，不要有其他說明文字。
"""

INGEST_USER_TEMPLATE = """請分析以下文件，產出 Wiki 知識頁面。

## 文件資訊

- 檔案名稱：{file_name}
- 萃取日期：{date}

## 文件內容

{content}
"""


# ── 核心函式 ─────────────────────────────────────────────────

async def run_ingest(
    document_id: int,
    file_path: str,
    file_name: str,
) -> dict:
    """執行 LLM Ingest 完整流程。

    Args:
        document_id: atwk_document 的 PK
        file_path:   原始文件的絕對路徑（raw/ 下）
        file_name:   原始檔名（用於顯示）

    Returns:
        {
            "success": bool,
            "ingest_id": int | None,
            "page_count": int,
            "pages": [{"path": str, "title": str}],
            "error": str | None,
        }
    """
    ingest_id: int | None = None
    ingest_start = datetime.now(timezone.utc)

    async with get_conn() as conn:
        # 建立 ingest log（status=R Running）
        ingest_id = await conn.fetchval(
            """
            INSERT INTO atwk_ingest_log (document_id, ingest_start, status, create_date)
            VALUES ($1, $2, 'R', NOW())
            RETURNING ingest_id
            """,
            document_id,
            ingest_start,
        )
        # 更新 document 狀態為 Running
        await conn.execute(
            "UPDATE atwk_document SET ingest_status='R', update_date=NOW() WHERE document_id=$1",
            document_id,
        )

    try:
        # ── 1. 萃取文字 ─────────────────────────────────────
        raw_text = extract_text(file_path)

        # ── 2. 呼叫 LLM ─────────────────────────────────────
        user_msg = INGEST_USER_TEMPLATE.format(
            file_name=file_name,
            date=datetime.now().strftime("%Y-%m-%d"),
            content=raw_text[:80000],  # 避免超出 context window
        )
        llm_response = await chat(
            messages=[
                {"role": "system", "content": INGEST_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=8192,
        )

        # ── 3. 解析 LLM 回應（JSON） ────────────────────────
        parsed = _parse_llm_json(llm_response)
        pages_data: list[dict] = parsed.get("pages", [])

        if not pages_data:
            raise ValueError("LLM 未回傳任何 wiki 頁面")

        # ── 4. 寫出 wiki 頁面檔案 + DB 索引 ─────────────────
        wiki_base = Path(settings.wiki_dir)
        created_pages: list[dict] = []

        async with get_conn() as conn:
            for page in pages_data:
                page_path: str  = page["page_path"].strip("/")
                page_title: str = page["page_title"]
                category: str   = page["category"]
                content: str    = page["content"]

                # 寫 md 檔案
                md_path = wiki_base / f"{page_path}.md"
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(content, encoding="utf-8")

                # 寫 DB（upsert by page_path）
                await conn.execute(
                    """
                    INSERT INTO atwk_wiki_page
                        (page_path, page_title, page_category, source_document_id, ingest_id, create_date)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (page_path) DO UPDATE SET
                        page_title   = EXCLUDED.page_title,
                        page_category = EXCLUDED.page_category,
                        ingest_id    = EXCLUDED.ingest_id,
                        is_delete    = 'N',
                        update_date  = NOW()
                    """,
                    page_path,
                    page_title,
                    category,
                    document_id,
                    ingest_id,
                )
                created_pages.append({"path": page_path, "title": page_title, "category": category})

        # ── 5. 更新 wiki/index.md ────────────────────────────
        await _update_wiki_index(created_pages)

        # ── 6. 更新 wiki/log.md ──────────────────────────────
        _append_wiki_log(
            action="INGEST",
            detail=f"{file_name} → 建立 {len(created_pages)} 個 wiki 頁",
        )

        # ── 7. 完成：更新 log + document 狀態 ────────────────
        ingest_end = datetime.now(timezone.utc)
        async with get_conn() as conn:
            await conn.execute(
                """
                UPDATE atwk_ingest_log
                SET status='S', ingest_end=$1, page_count=$2
                WHERE ingest_id=$3
                """,
                ingest_end, len(created_pages), ingest_id,
            )
            await conn.execute(
                "UPDATE atwk_document SET ingest_status='D', update_date=NOW() WHERE document_id=$1",
                document_id,
            )

        return {
            "success": True,
            "ingest_id": ingest_id,
            "page_count": len(created_pages),
            "pages": created_pages,
            "error": None,
        }

    except Exception as e:
        # 失敗：寫 error 記錄
        error_msg = str(e)
        if ingest_id:
            async with get_conn() as conn:
                await conn.execute(
                    """
                    UPDATE atwk_ingest_log
                    SET status='E', ingest_end=NOW(), error_msg=$1
                    WHERE ingest_id=$2
                    """,
                    error_msg, ingest_id,
                )
                await conn.execute(
                    "UPDATE atwk_document SET ingest_status='E', update_date=NOW() WHERE document_id=$1",
                    document_id,
                )
        return {
            "success": False,
            "ingest_id": ingest_id,
            "page_count": 0,
            "pages": [],
            "error": error_msg,
        }


# ── 輔助函式 ─────────────────────────────────────────────────

def _parse_llm_json(text: str) -> dict:
    """從 LLM 回應中萃取 JSON。

    LLM 有時會包上 ```json ... ``` fenced block，需要去除。
    """
    # 嘗試直接 parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 找 fenced block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"無法解析 LLM 回應為 JSON：{text[:200]}…")


async def _update_wiki_index(new_pages: list[dict]) -> None:
    """將新頁面加入 wiki/index.md。

    若頁面已存在於 index 中則跳過，避免重複。
    """
    index_path = Path(settings.wiki_dir) / "index.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")

    # 按 category 分組
    by_category: dict[str, list[dict]] = {}
    for page in new_pages:
        cat = page["category"]
        by_category.setdefault(cat, []).append(page)

    CATEGORY_HEADERS = {
        "concepts":     "## 概念頁（concepts/）",
        "operations":   "## 操作流程頁（operations/）",
        "architecture": "## 架構頁（architecture/）",
        "sources":      "## 來源摘要頁（sources/）",
        "syntheses":    "## 綜合分析頁（syntheses/）",
    }

    lines = content.splitlines()
    for cat, pages in by_category.items():
        header = CATEGORY_HEADERS.get(cat)
        if not header:
            continue
        for page in pages:
            link = f"[[{page['path']}]]"
            new_row = f"| {link} | {page['title']} |"
            # 已存在則跳過
            if link in content:
                continue
            # 找到 header 所在行，在下一個表格結尾前插入
            try:
                idx = next(i for i, l in enumerate(lines) if header in l)
                # 找表格最後一行
                insert_at = idx + 1
                while insert_at < len(lines) and (
                    lines[insert_at].startswith("|") or
                    lines[insert_at].strip() in ("", "| 頁面 | 摘要 |", "|------|------|")
                ):
                    insert_at += 1
                lines.insert(insert_at, new_row)
                content = "\n".join(lines)
                lines = content.splitlines()
            except StopIteration:
                # 找不到 header，附加到文末
                content += f"\n{header}\n\n| 頁面 | 摘要 |\n|------|------|\n{new_row}\n"
                lines = content.splitlines()

    index_path.write_text(content, encoding="utf-8")


def _append_wiki_log(action: str, detail: str) -> None:
    """在 wiki/log.md 末尾新增一行操作記錄。"""
    log_path = Path(settings.wiki_dir) / "log.md"
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"{date_str} | {action} | {detail}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
