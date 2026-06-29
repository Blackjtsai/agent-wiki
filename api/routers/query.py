# ============================================================
# 檔案名稱：query.py
# 中文名稱：知識查詢 API 路由
# 功能說明：POST /api/query — 自然語言查詢 wiki，LLM 綜合回答
# 所屬模組：api/routers/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.config import settings
from api.llm import chat

router = APIRouter(tags=["Query"])


# ── Request / Response Schema ────────────────────────────────

class QueryRequest(BaseModel):
    """查詢請求。"""
    q: str = Field(..., min_length=1, max_length=1000, description="自然語言問題")


class SourceRef(BaseModel):
    """來源參照。"""
    path: str   = Field(..., description="wiki 頁面路徑")
    title: str  = Field(..., description="頁面標題")


class QueryResponse(BaseModel):
    """查詢回應。"""
    answer: str             = Field(..., description="LLM 回答")
    sources: list[SourceRef] = Field(default_factory=list, description="使用的 wiki 來源")


# ── Prompt 定義 ──────────────────────────────────────────────

QUERY_SYSTEM_PROMPT = """你是一個知識庫查詢助理。
請根據提供的 Wiki 知識庫內容，精確回答使用者的問題。

## 規則

1. 只使用提供的 Wiki 內容作答，不要加入外部知識
2. 若 Wiki 內容不足以回答，明確說明「查無相關資料」
3. 回答使用繁體中文，語氣專業簡潔
4. 最後列出使用的來源頁面（格式見下）

## 輸出格式（嚴格 JSON）

```json
{
  "answer": "你的回答內容",
  "sources": [
    {"path": "wiki 頁面路徑", "title": "頁面標題"},
    ...
  ]
}
```

sources 只列出真正被用來回答的頁面，不要虛構。
只輸出 JSON，不要有其他說明文字。
"""


# ── Router ───────────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse, summary="自然語言知識查詢")
async def query(request: QueryRequest) -> QueryResponse:
    """接收自然語言問題，讀取 wiki 知識庫後由 LLM 回答。

    Args:
        request: 含 `q`（問題）的請求體

    Returns:
        QueryResponse: LLM 回答 + 來源列表
    """
    if not request.q.strip():
        raise HTTPException(status_code=400, detail="請輸入問題")

    # ── 1. 讀取 wiki 內容 ────────────────────────────────────
    wiki_context, page_index = _load_wiki_context()

    if not wiki_context:
        return QueryResponse(
            answer="知識庫目前尚無內容，請先執行 Ingest 上架文件。",
            sources=[],
        )

    # ── 2. 呼叫 LLM ─────────────────────────────────────────
    user_msg = f"## Wiki 知識庫內容\n\n{wiki_context}\n\n## 使用者問題\n\n{request.q}"

    try:
        llm_response = await chat(
            messages=[
                {"role": "system", "content": QUERY_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"LLM 服務暫時不可用：{e}")

    # ── 3. 解析回應 ──────────────────────────────────────────
    try:
        import json, re
        # 去除 fenced block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", llm_response)
        if match:
            raw = match.group(1)
        else:
            raw = llm_response

        parsed = json.loads(raw)
        answer  = parsed.get("answer", "")
        sources = [SourceRef(**s) for s in parsed.get("sources", [])]
    except Exception:
        # 解析失敗：回傳原始文字，無 sources
        answer  = llm_response
        sources = []

    # 防止 sources 列出不存在的頁面
    sources = [s for s in sources if s.path in page_index]

    return QueryResponse(answer=answer, sources=sources)


# ── 輔助函式 ─────────────────────────────────────────────────

def _load_wiki_context() -> tuple[str, dict[str, str]]:
    """讀取所有 wiki 頁面內容，組合成 LLM context 字串。

    Returns:
        (wiki_context_str, page_index)
        page_index: {page_path: page_title}
    """
    wiki_base = Path(settings.wiki_dir)
    if not wiki_base.exists():
        return "", {}

    pages: list[tuple[str, str, str]] = []  # (path, title, content)
    page_index: dict[str, str] = {}

    # 讀取 index.md 取得頁面清單與標題
    index_path = wiki_base / "index.md"
    if index_path.exists():
        import re
        index_content = index_path.read_text(encoding="utf-8")
        # 解析 wikilinks：[[category/page_name]]
        for match in re.finditer(r"\[\[([^\]]+)\]\]\s*\|\s*([^|]+)\|", index_content):
            page_path = match.group(1).strip()
            page_title = match.group(2).strip()
            page_index[page_path] = page_title

    # 讀取所有 .md 頁面（跳過 index.md / log.md / WIKI-RULES.md）
    skip_files = {"index.md", "log.md", "WIKI-RULES.md", "overview.md"}
    total_chars = 0
    MAX_CONTEXT_CHARS = 100_000  # 約 50k tokens，保留 context 空間

    for md_file in sorted(wiki_base.rglob("*.md")):
        if md_file.name in skip_files:
            continue
        rel_path = md_file.relative_to(wiki_base).with_suffix("").as_posix()
        content = md_file.read_text(encoding="utf-8")

        # 從第一行 # 標題取得 title（若 index 未收錄）
        first_line = content.splitlines()[0] if content.strip() else ""
        title = first_line.lstrip("#").strip() if first_line.startswith("#") else rel_path
        page_index.setdefault(rel_path, title)

        if total_chars + len(content) > MAX_CONTEXT_CHARS:
            break
        pages.append((rel_path, title, content))
        total_chars += len(content)

    if not pages:
        return "", page_index

    # 組合 context
    sections = []
    for path, title, content in pages:
        sections.append(f"### [{title}] (path: {path})\n\n{content}")

    return "\n\n---\n\n".join(sections), page_index
