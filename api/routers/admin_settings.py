# ============================================================
# 檔案名稱：admin_settings.py
# 中文名稱：LLM 設定管理 API
# 功能說明：提供後台 LLM 設定的讀取、in-memory 更新與連線測試
# 所屬模組：api/routers/
# 建立日期：2026-06-29
# 修改日期：2026-06-29
# 開發者　：Blackjtsai
# ============================================================

import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.config import settings
from api.dependencies import require_admin
from api.llm import chat

router = APIRouter(tags=["Admin - Settings"], dependencies=[Depends(require_admin)])


# ── Schemas ──────────────────────────────────────────────────

class LLMConfig(BaseModel):
    """單一角色的 LLM 設定（api_key 只回傳是否已設定）。"""
    role: str
    model: str
    api_key_set: bool
    base_url: str


class LLMSettingsResponse(BaseModel):
    """雙 LLM 設定回應。"""
    ingest: LLMConfig
    query: LLMConfig


class LLMUpdateRequest(BaseModel):
    """更新單一角色的 LLM 設定。"""
    role: str           # "ingest" | "query"
    model: str
    api_key: str = ""
    base_url: str = ""


class LLMUpdateResponse(BaseModel):
    success: bool
    message: str


class TestRequest(BaseModel):
    role: str  # "ingest" | "query"


class TestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int


# ── Routes ───────────────────────────────────────────────────

@router.get("/settings/llm", response_model=LLMSettingsResponse, summary="讀取雙 LLM 設定")
async def get_llm_settings() -> LLMSettingsResponse:
    """讀取 Ingest 與 Query 兩組 LLM 當前設定。

    api_key 欄位只回傳是否已設定（true/false），不回傳原始值。

    Returns:
        LLMSettingsResponse: 兩組 LLM 設定
    """
    return LLMSettingsResponse(
        ingest=LLMConfig(
            role="ingest",
            model=settings.ingest_model,
            api_key_set=bool(settings.ingest_api_key),
            base_url=settings.ingest_base_url,
        ),
        query=LLMConfig(
            role="query",
            model=settings.query_model,
            api_key_set=bool(settings.query_api_key),
            base_url=settings.query_base_url,
        ),
    )


@router.patch("/settings/llm", response_model=LLMUpdateResponse, summary="更新 LLM 設定（in-memory）")
async def update_llm_settings(body: LLMUpdateRequest) -> LLMUpdateResponse:
    """更新指定角色的 LLM 設定（僅影響當前進程，重啟後恢復 .env 值）。

    Args:
        body: 包含 role（ingest|query）、model、api_key、base_url

    Returns:
        LLMUpdateResponse: 操作結果
    """
    if body.role == "ingest":
        settings.llm_ingest_model   = body.model
        if body.api_key:
            settings.llm_ingest_api_key = body.api_key
        settings.llm_ingest_base_url = body.base_url
    elif body.role == "query":
        settings.llm_query_model    = body.model
        if body.api_key:
            settings.llm_query_api_key  = body.api_key
        settings.llm_query_base_url  = body.base_url
    else:
        raise HTTPException(status_code=400, detail=f"不支援的 role：{body.role}，請填 ingest 或 query")

    return LLMUpdateResponse(
        success=True,
        message=f"{body.role} LLM 已套用為 {body.model}（重啟後恢復 .env 設定）",
    )


@router.post("/settings/llm/test", response_model=TestResult, summary="測試 LLM 連線")
async def test_llm_connection(body: TestRequest) -> TestResult:
    """向指定角色的 LLM 發送測試請求，回傳成功/失敗與延遲。

    Args:
        body: 包含 role（ingest|query）

    Returns:
        TestResult: 成功、訊息、延遲毫秒數
    """
    if body.role == "ingest":
        model   = settings.ingest_model
        api_key = settings.ingest_api_key
        base_url = settings.ingest_base_url
    elif body.role == "query":
        model   = settings.query_model
        api_key = settings.query_api_key
        base_url = settings.query_base_url
    else:
        raise HTTPException(status_code=400, detail=f"不支援的 role：{body.role}")

    start = time.monotonic()
    try:
        await chat(
            messages=[{"role": "user", "content": "回應 OK 兩字即可"}],
            max_tokens=10,
            model=model,
            api_key=api_key or None,
            base_url=base_url or None,
        )
        latency = int((time.monotonic() - start) * 1000)
        return TestResult(success=True, message=f"連線成功（{model}）", latency_ms=latency)
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return TestResult(success=False, message=str(e)[:200], latency_ms=latency)
