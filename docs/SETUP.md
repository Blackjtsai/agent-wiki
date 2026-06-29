# ATWK — 環境安裝說明

## 前置需求

| 項目 | 版本 | 說明 |
|------|------|------|
| Python | 3.12+ | 主程式語言 |
| uv | 最新 | 套件管理 |
| PostgreSQL | 14+ | 主資料庫 |
| LiteLLM | — | LLM Proxy（或直接 API key） |

## 安裝步驟

### 1. 複製設定檔

```bash
cp .env.example .env
# 編輯 .env，填入 DB 連線與 LLM API key
```

### 2. 建立虛擬環境與安裝套件

```bash
uv sync
```

### 3. 建立資料庫

```bash
# 以 psql 登入
createdb db_atwk
psql -d db_atwk -f db/migration_001_init.sql
```

### 4. 建立 wiki 目錄

```bash
mkdir -p inbox raw wiki templates
```

### 5. 啟動服務

```bash
uv run uvicorn api.main:app --reload --port 8300
```

### 6. 驗證

```bash
curl http://localhost:8300/health
# 預期回傳：{"status": "ok", "service": "ATWK"}
```

## .env 必要欄位

```
# DB
ATWK_DB_HOST=localhost
ATWK_DB_PORT=5432
ATWK_DB_NAME=db_atwk
ATWK_DB_USER=
ATWK_DB_PASSWORD=

# LLM
ATWK_LLM_MODEL=claude-sonnet-4-6
ATWK_LLM_API_KEY=

# Service
ATWK_PORT=8300
ATWK_SECRET_KEY=

# AgentPULSE（Layer 6 後填）
APMS_BASE_URL=
APMS_AGENT_ID=
```

## 常見問題

| 問題 | 排查 |
|------|------|
| DB 連線失敗 | 確認 PostgreSQL 已啟動，確認 .env 帳密 |
| Port 8300 被占用 | `lsof -i :8300` 找到 PID 後 kill |
| LLM 回傳錯誤 | 確認 API key 與 model 名稱正確 |
