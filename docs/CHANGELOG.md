# ATWK — 變更記錄

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
