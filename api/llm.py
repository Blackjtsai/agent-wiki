# ============================================================
# 檔案名稱：llm.py
# 中文名稱：LLM 呼叫封裝
# 功能說明：統一封裝 LiteLLM 呼叫，供 ingest 與 query 模組共用
# 所屬模組：api/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

import litellm
from api.config import settings


async def chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 8192,
) -> str:
    """呼叫 LLM 並回傳文字回應。

    Args:
        messages: OpenAI 格式的 messages list
        temperature: 溫度（預設 0.3，降低隨機性）
        max_tokens: 最大 token 數

    Returns:
        LLM 回傳的文字內容

    Raises:
        RuntimeError: LLM 呼叫失敗時
    """
    kwargs: dict = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # 設定 API key
    if settings.llm_api_key:
        kwargs["api_key"] = settings.llm_api_key

    # 若有設定 proxy base_url
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url

    try:
        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM 回傳空內容")
        return content
    except Exception as e:
        raise RuntimeError(f"LLM 呼叫失敗：{e}") from e


async def check_llm_health() -> bool:
    """簡單測試 LLM 是否可用，回傳 True / False。"""
    try:
        await chat(
            messages=[{"role": "user", "content": "回應 OK 兩字即可"}],
            max_tokens=10,
        )
        return True
    except Exception:
        return False
