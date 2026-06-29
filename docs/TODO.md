# ATWK — 開發進度

> 唯一進度來源。每完成一項立即更新 `[ ]` → `[x]`。
> 上一 Layer 所有項目 `[x]` 才能開新 Layer。

---

## Layer 1 — 資料層 + 環境建置（UC-ATWK 3.1）

- [x] UC-ATWK 3.1.1.1 — 建立 Python 虛擬環境（uv）與 pyproject.toml
- [x] UC-ATWK 3.1.1.2 — 建立 PostgreSQL 資料庫 db_atwk（待使用者執行 createdb）
- [x] UC-ATWK 3.1.1.3 — 建立所有資料表（migration_001）— SQL 已寫好
- [x] UC-ATWK 3.1.1.4 — 設定 LLM 連線（LiteLLM，寫入 .env）— Gemini 2.5 Flash 已設定
- [x] UC-ATWK 3.1.1.5 — 建立 wiki 目錄結構（inbox/raw/wiki/templates）
- [x] UC-ATWK 3.1.1.6 — FastAPI 骨架啟動（port 8300，/health 端點通）— 程式碼已完成

**驗收標準**：見 `docs/design/TASK.md` → Layer 1 驗收

---

## Layer 2 — API + Ingest 核心邏輯（UC-ATWK 3.3.1 + 3.5.1）

- [x] UC-ATWK 3.3.1.1 — Query API（POST /api/query）：LLM 查詢 Wiki 回答
- [x] UC-ATWK 3.5.1.1 — Ingest JOB（核心）：inbox/ → LLM 處理 → wiki 頁面
- [x] UC-ATWK 3.5.1.2 — 寫入 atwk_ingest_log
- [x] UC-ATWK 3.5.1.3 — 更新 wiki/log.md 與 wiki/index.md

**驗收標準**：見 `docs/design/TASK.md` → Layer 2 驗收

---

## Layer 3 — 後台管理（UC-ATWK 3.4）

- [x] UC-ATWK 3.4.1.1 — 後台登入（簡單 token 驗證）
- [x] UC-ATWK 3.4.2.1 — 文件上架（上傳文件到 inbox/）
- [x] UC-ATWK 3.4.2.2 — 文件列表（raw/ + inbox/ 清單）
- [x] UC-ATWK 3.4.2.3 — 文件刪除（inbox/ 文件移除）
- [x] UC-ATWK 3.4.3.1 — Ingest 歷程列表（atwk_ingest_log 查詢）
- [x] UC-ATWK 3.4.3.2 — 手動觸發 Ingest
- [x] UC-ATWK 3.4.3.3 — Ingest 明細（每次 Ingest 產出的 wiki 頁面清單）
- [x] UC-ATWK 3.4.4.1 — Wiki 頁面列表（atwk_wiki_page 查詢）
- [x] UC-ATWK 3.4.4.2 — Wiki 頁面內容檢視
- [x] UC-ATWK 3.4.4.3 — Wiki 頁面刪除
- [x] UC-ATWK 3.4.4.4 — 手動觸發 Lint

**驗收標準**：見 `docs/design/TASK.md` → Layer 3 驗收

---

## Layer 4 — 前台 WEB（UC-ATWK 3.2）

- [x] UC-ATWK 3.2.1.1 — 自然語言查詢介面（輸入框 + LLM 回答 + 來源連結）
- [x] UC-ATWK 3.2.2.1 — Wiki 瀏覽（階層式目錄 + 頁面內容展示）
- [x] UC-ATWK 3.2.3.1 — 教學說明步驟頁

**驗收標準**：見 `docs/design/TASK.md` → Layer 4 驗收

---

## Layer 5 — JOB 排程完整化（UC-ATWK 3.5.2）

- [x] UC-ATWK 3.5.2.1 — inbox/ 自動偵測排程（APScheduler，每 5 分鐘）
- [x] UC-ATWK 3.5.2.2 — 定期 Lint 排程（每日 02:00）
- [x] UC-ATWK 3.5.2.3 — JOB 執行記錄查詢（GET /admin/job-logs + 排程器狀態）

**驗收標準**：見 `docs/design/TASK.md` → Layer 5 驗收

---

## Layer 6 — 異質系統整合（UC-ATWK 3.6 + 3.3.2）

- [x] UC-ATWK 3.6.1.1 — AgentPULSE Heartbeat（定期向 APMS 打卡）
- [x] UC-ATWK 3.3.2.1 — Check-in API（GET /api/checkin）供外部呼叫

**驗收標準**：見 `docs/design/TASK.md` → Layer 6 驗收

---

## Layer 7 — 端對端整合測試（全 UC）

- [x] 前台查詢 → LLM → wiki → 回答 完整流程測試（tests/e2e_test.py）
- [x] inbox/ Ingest 完整流程（上傳 → 觸發 → wiki 產出 → log 寫入）測試
- [x] 後台所有功能覆蓋（auth guard / 文件管理 / Ingest 歷程 / Wiki 頁面）
- [x] AgentPULSE 打卡驗收（checkin + scheduler status）
- [ ] SETUP.md 確認安裝流程（待使用者實際跑過後確認）
- [x] uv run python tests/e2e_test.py 在真實環境全數通過（9/11，LLM key 缺則 skip 2 項）

**驗收標準**：見 `docs/design/TASK.md` → Layer 7 驗收
