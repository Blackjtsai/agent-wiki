# ATWK — Layer 驗收條件（TASK.md）

> 每個 Layer 開始前必須填寫驗收條件。未填寫 = 不可開始。

---

## Layer 1 驗收 — 資料層 + 環境建置

**成功標準（全部達成才算完成）：**

1. ✅ `uv run uvicorn api.main:app --port 8300` 正常啟動，無 import error
2. ✅ `curl http://localhost:8300/health` → `{"status":"ok","service":"ATWK"}`
3. ✅ `psql -d db_atwk -c "\dt"` 顯示 4 張表（atwk_document / atwk_ingest_log / atwk_wiki_page / atwk_job_log）
4. ✅ `.env` 中 LLM API key 可呼叫 LiteLLM 回傳正常
5. ✅ `inbox/` `raw/` `wiki/` `templates/` 目錄存在

**Error path：**
- DB 連線失敗 → `/health` 回傳 `{"status":"error","detail":"db connection failed"}`
- LLM API key 無效 → `/health` 回傳 `{"status":"warning","detail":"llm not configured"}`

---

## Layer 2 驗收 — API + Ingest 核心邏輯

**成功標準：**

1. ✅ 手動將測試文件放入 `inbox/`，呼叫 Ingest 核心函式 → `wiki/` 下產出對應 md 頁面
2. ✅ `atwk_ingest_log` 有寫入一筆記錄，status = 'S'
3. ✅ `wiki/log.md` 有新增一行 INGEST 記錄
4. ✅ `wiki/index.md` 有更新（新頁面出現在對應分類下）
5. ✅ `POST /api/query {"q":"xxx"}` → LLM 讀取 wiki 後回傳答案，有 `sources` 欄位

**Error path：**
- Ingest 中 LLM 呼叫失敗 → log status = 'E'，error_msg 有內容，不產出 wiki 頁
- Query API 無相關 wiki 內容 → 回傳 `{"answer":"查無相關資料","sources":[]}`

---

## Layer 3 驗收 — 後台管理

**成功標準：**

1. ✅ `POST /admin/login` 帶正確 token → 回傳 `{"success":true}`
2. ✅ 後台頁面可開啟（瀏覽器直接打開 HTML 檔案）
3. ✅ 上傳 .pptx 檔案 → 出現在 inbox/ 資料夾，文件列表頁可見
4. ✅ Ingest 歷程列表顯示 Layer 2 產出的記錄
5. ✅ 手動觸發 Ingest → 新文件被處理，Wiki 頁面列表增加
6. ✅ Wiki 頁面列表顯示全部頁面，可查看內容（Markdown 渲染）
7. ✅ 刪除 Wiki 頁面 → is_delete='Y'，列表消失

**Error path：**
- 無效 token 打後台 API → 401 Unauthorized
- 上傳非支援格式 → 400 回傳 `{"error":"不支援的檔案格式"}`

---

## Layer 4 驗收 — 前台 WEB

**成功標準：**

1. ✅ 前台頁面可在瀏覽器開啟（Vue 3 CDN）
2. ✅ 輸入查詢問題 → 呼叫 `/api/query` → 顯示 LLM 回答
3. ✅ 回答下方顯示來源 wiki 頁面連結
4. ✅ Wiki 瀏覽頁：左側目錄樹，右側頁面內容（Markdown 渲染）
5. ✅ 教學說明頁：步驟式說明系統使用方式

**Error path：**
- API 無回應 → 前台顯示「服務暫時不可用，請稍後再試」
- 查詢空字串 → 前台提示「請輸入問題」，不發 API

---

## Layer 5 驗收 — JOB 排程完整化

**成功標準：**

1. ✅ 服務啟動後，APScheduler 自動每 5 分鐘掃描 inbox/
2. ✅ 放文件進 inbox/ → 5 分鐘內自動 Ingest，wiki 頁面產出
3. ✅ 每日 Lint JOB 可在後台觸發（並驗證定時執行）
4. ✅ `atwk_job_log` 有 inbox_scan 記錄

**Error path：**
- APScheduler 某次執行失敗 → job_log status = 'E'，不影響下次排程

---

## Layer 6 驗收 — 異質系統整合

**成功標準：**

1. ✅ `GET /api/checkin` → `{"agent":"ATWK","status":"ok","timestamp":"..."}`
2. ✅ AgentPULSE 後台可看到 ATWK 的打卡記錄

**Error path：**
- APMS 服務無法連線 → Heartbeat JOB 寫 job_log error，服務本身不中斷

---

## Layer 7 驗收 — 端對端整合測試

**成功標準：**

1. ✅ 完整流程：上傳 .pptx → inbox/ 偵測 → Ingest → wiki 頁產出 → 前台查詢到新知識
2. ✅ 後台歷程完整（document / ingest_log / wiki_page / job_log 資料一致）
3. ✅ AgentPULSE 可看到 ATWK 定期打卡
4. ✅ `docs/SETUP.md` 按步驟安裝完後，系統可正常啟動
5. ✅ `docs/CHANGELOG.md` 更新至正式版本

---

## 尚未填寫的 Layer

_（以上 Layer 1-7 為初始規劃，如新增 Layer 需在此追加）_
