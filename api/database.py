# ============================================================
# 檔案名稱：database.py
# 中文名稱：資料庫連線管理
# 功能說明：asyncpg 連線池初始化與取得，提供 get_pool / get_conn
# 所屬模組：api/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from api.config import settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    """建立全域連線池（在 app lifespan 啟動時呼叫）。"""
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.db_dsn,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )


async def close_pool() -> None:
    """關閉全域連線池（在 app lifespan 結束時呼叫）。"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """取得全域連線池（若尚未初始化則拋出例外）。"""
    if _pool is None:
        raise RuntimeError("DB pool 尚未初始化，請確認 lifespan 已執行 init_pool()")
    return _pool


@asynccontextmanager
async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """從連線池借出一個連線，使用完畢後自動歸還。

    用法：
        async with get_conn() as conn:
            row = await conn.fetchrow("SELECT 1")
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def check_db_health() -> bool:
    """確認 DB 連線是否正常，回傳 True / False。"""
    try:
        async with get_conn() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
