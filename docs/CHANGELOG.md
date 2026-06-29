# ATWK — 變更記錄

---

## [0.8.0] 2026-06-29

### 後台儀表板 + LLM 雙角色設定 + ARCHITECTURE 升級

- 新增 `api/routers/admin_dashboard.py`：GET /admin/dashboard，彙整服務狀態 / 資料統計 / 磁碟使用 / 排程器 / 最近 Ingest
- 新增 `api/routers/admin_settings.py`：GET /PATCH /admin/settings/llm + POST /admin/settings/llm/test，後台即時切換 Ingest / Query LLM 模型
- 更新 `backend/admin.html`：新增「📊 儀表板」Tab 與「⚙️ LLM 設定」Tab（支援雙角色切換 + 連線測試）
- 更新 `api/llm.py`：新增 `chat_ingest()` / `chat_query()` 雙角色 wrapper，chat() 支援 model/api_key/base_url 覆寫
- 更新 `api/config.py`：新增 `ingest_*` / `query_*` 9 個 properties，含 fallback 到共用設定邏輯
- 更新 `.env.example`：新增 Ingest / Query 雙 LLM 環境變數欄位說明
- 更新 `docs/design/ARCHITECTURE.md`：完整重寫，新增 sequence diagram（Ingest / Query）、erDiagram（4 張表）、HTML API 總覽表、Layer 狀態表、LLM 路由策略表、模組對應表；增加文字流程摘要

---

## [0.7.0] 2026-06-29

### Layer 7 — 端對端整合測試通過

- 修正 PostgreSQL 認證：`pg_hba.conf` 加入 127.0.0.1 trust 規則，postgres 密碼設為 `123`
- 執行 `tests/e2e_test.py` 全流程驗收：9/11 pass（2 項需 LLM API key，預期 skip）
- 初始化 git repo，推送 77 個檔案至 GitHub（https://github.com/Blackjtsai/agent-wiki）

---

## [0.6.0] 2026-06-28

### Layer 6 — 異質系統整合

- 新增 `external/agentpulse.py`：AgentPULSE 打卡客戶端（send_heartbeat / collect_health_detail）
- 新增 `api/routers/checkin.py`：GET /api/checkin，回傳服務健康狀態並觸發打卡
- 啟用 APScheduler heartbeat JOB（每 10 分鐘向 APMS 打卡）
- `api/main.py` 掛載 checkin router

---

## [0.5.0] 2026-06-28

### Layer 5 — JOB 排程完整化

- 新增 `job/inbox_scan.py`：每 5 分鐘掃描 inbox/，自動 move → DB 記錄 → 觸發 Ingest
- 新增 `job/scheduler.py`：APScheduler 初始化，3 個 JOB（inbox_scan / daily_lint / heartbeat）
- 強化 `job/lint.py`：完整 Lint 邏輯（H1 標題 / wikilinks 有效性 / 最後更新區塊 / job_log）
- 新增 `api/routers/admin_jobs.py`：GET /admin/job-logs + GET /admin/scheduler/status
- 更新 `backend/admin.html`：JOB Tab 接上真實 API，加排程狀態卡片
- `api/main.py` 整合 APScheduler lifespan 啟動 / 關閉

---

## [0.4.0] 2026-06-28

### Layer 4 — 前台 WEB

- 新增 `api/routers/wiki_public.py`：GET /api/wiki-pages + GET /api/wiki-pages/{id}（公開，無需 Token）
- 新增 `frontend/index.html`：Vue 3 CDN 前台，三個 Tab（查詢 / Wiki 瀏覽 / 教學說明）
- 查詢 Tab：自然語言 → /api/query → LLM 回答 + 來源連結（可跳至 Wiki 瀏覽）
- Wiki 瀏覽 Tab：分類目錄樹 + Markdown 渲染
- 教學說明 Tab：4 個步驟卡片

---

## [0.3.0] 2026-06-28

### Layer 3 — 後台管理

- 新增 `api/dependencies.py`：Bearer Token 驗證 Depends
- 新增 `api/routers/admin_auth.py`：POST /admin/login
- 新增 `api/routers/admin_documents.py`：文件上傳 / 列表 / 刪除
- 新增 `api/routers/admin_ingest.py`：Ingest 歷程 / 手動觸發 / 明細
- 新增 `api/routers/admin_wiki.py`：Wiki 頁面列表 / 檢視 / 刪除 / Lint
- 新增 `job/lint.py`（stub）
- 新增 `backend/admin.html`：後台管理 UI（Vue 3 CDN，登入 + 4 個 Tab）

---

## [0.2.0] 2026-06-28

### Layer 2 — API + Ingest 核心邏輯

- 新增 `api/llm.py`：LiteLLM 統一封裝（chat / check_llm_health）
- 新增 `job/parsers.py`：pptx / docx / pdf / txt 文字萃取
- 新增 `job/ingest.py`：LLM Ingest 核心（文件解析 → LLM → wiki 頁產出 → DB log → index 更新）
- 新增 `api/routers/query.py`：POST /api/query（自然語言查詢，LLM 讀 wiki 回答）

---

## [0.1.0] 2026-06-28

### Layer 1 — 資料層 + 環境建置

- 建立 `pyproject.toml`（Python 3.12 + FastAPI + asyncpg + LiteLLM + APScheduler）
- 建立 `db/migration_001_init.sql`：4 張表（atwk_document / atwk_ingest_log / atwk_wiki_page / atwk_job_log）
- 建立 `api/config.py`、`api/database.py`、`api/routers/health.py`、`api/main.py`
- 建立 `wiki/`、`raw/`、`inbox/`、`templates/` 目錄結構

### 初始化

- 建立 new-project-init 骨架（CLAUDE.md / docs/ / .claude/commands/）
- 建立 wiki 知識庫基礎結構
- 完成首次 Ingest：Portal_20260209.pptx → 7 個 wiki 頁面
- 系統代號 ATWK，Port 8300，DB db_atwk
