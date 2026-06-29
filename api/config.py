# ============================================================
# 檔案名稱：config.py
# 中文名稱：系統設定
# 功能說明：讀取 .env 環境變數，統一提供設定物件
# 所屬模組：api/
# 建立日期：2026-06-28
# 修改日期：2026-06-28
# 開發者　：Blackjtsai
# ============================================================

from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    """系統設定物件，從 .env 讀取所有設定值。"""

    # ── 資料庫 ──────────────────────────────────────────────
    db_host: str     = os.getenv("ATWK_DB_HOST", "localhost")
    db_port: int     = int(os.getenv("ATWK_DB_PORT", "5432"))
    db_name: str     = os.getenv("ATWK_DB_NAME", "db_atwk")
    db_user: str     = os.getenv("ATWK_DB_USER", "")
    db_password: str = os.getenv("ATWK_DB_PASSWORD", "")

    @property
    def db_dsn(self) -> str:
        """asyncpg 連線字串。"""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── LLM ─────────────────────────────────────────────────
    llm_model: str    = os.getenv("ATWK_LLM_MODEL", "claude-sonnet-4-6")
    llm_api_key: str  = os.getenv("ATWK_LLM_API_KEY", "")
    llm_base_url: str = os.getenv("ATWK_LLM_BASE_URL", "")

    # ── 服務 ────────────────────────────────────────────────
    port: int           = int(os.getenv("ATWK_PORT", "8300"))
    secret_key: str     = os.getenv("ATWK_SECRET_KEY", "change-me-in-production")

    # ── AgentPULSE ──────────────────────────────────────────
    apms_base_url: str  = os.getenv("APMS_BASE_URL", "")
    apms_agent_id: str  = os.getenv("APMS_AGENT_ID", "")

    # ── Wiki 目錄 ────────────────────────────────────────────
    wiki_dir: str   = os.getenv("ATWK_WIKI_DIR", "wiki")
    raw_dir: str    = os.getenv("ATWK_RAW_DIR", "raw")
    inbox_dir: str  = os.getenv("ATWK_INBOX_DIR", "inbox")


settings = Settings()
