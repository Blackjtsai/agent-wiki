# ============================================================
# 檔案名稱：llm.py
# 中文名稱：LLM 呼叫封裝
# 功能說明：統一封裝 LiteLLM 呼叫，提供 Ingest / Query 雙角色 wrapper
# 所屬模組：api/
# 建立日期：2026-06-28
# 修改日期：2026-06-29
# 開發者　：Blackjtsai
# ============================================================

import litellm
from api.config import settings


async def chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 8192,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """呼叫 LLM 並回傳文字回應。

    Args:
        messages:    OpenAI 格式的 messages list
        temperature: 溫度（預設 0.3，降低隨機性）
        max_tokens:  最大 token 數
        model:       覆寫模型名稱（None 時使用 settings.llm_model）
        api_key:     覆寫 API key
        base_url:    覆寫 LiteLLM Proxy base_url

    Returns:
        LLM 回傳的文字內容

    Raises:
        RuntimeError: LLM 呼叫失敗時
    """
    kwargs: dict = {
        "model":       model    or settings.llm_model,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }

    resolved_key     = api_key   or settings.llm_api_key
    resolved_baseurl = base_url  or settings.llm_base_url

    if resolved_key:
        kwargs["api_key"] = resolved_key
    if resolved_baseurl:
        kwargs["base_url"] = resolved_baseurl

    try:
        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM 回傳空內容")
        return content
    except Exception as e:
        raise RuntimeError(f"LLM 呼叫失敗：{e}") from e


async def chat_ingest(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> str:
    """Ingest 專用 LLM 呼叫（使用 settings.ingest_model）。

    適合文件分析、結構化 JSON 輸出等需要強推理的任務。
    """
    return await chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=settings.ingest_model,
        api_key=settings.ingest_api_key,
        base_url=settings.ingest_base_url,
    )


async def chat_query(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> str:
    """Query 專用 LLM 呼叫（使用 settings.query_model）。

    適合前台問答，優先考慮回應速度。
    """
    return await chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=settings.query_model,
        api_key=settings.query_api_key,
        base_url=settings.query_base_url,
    )


async def check_llm_health(role: str = "query") -> bool:
    """測試指定角色的 LLM 是否可用，回傳 True / False。

    Args:
        role: "ingest" | "query"（預設 "query"）
    """
    caller = chat_ingest if role == "ingest" else chat_query
    try:
        await caller(
            messages=[{"role": "user", "content": "回應 OK 兩字即可"}],
            max_tokens=10,
        )
        return True
    except Exception:
        return False
