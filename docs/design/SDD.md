# ATWK — 系統設計說明書（SDD）

**系統代號**：ATWK  
**版本**：v0.1  
**日期**：2026-06-28  
**作者**：Blackjtsai

---

## 1. 系統概述

智能知識庫管理系統（ATWK），部門層級 AI 知識庫。原始文件（PPT/Word/PDF/TXT）經 LLM Ingest 整理成結構化 Wiki 頁面，提供自然語言查詢前台與後台管理介面，作為獨立數位員工與 AgentHQ 生態整合。

---

## 2. UC 清單

### UC-ATWK 3.1 — 基礎建設

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.1.1.1 | 建立虛擬環境 | uv 初始化，pyproject.toml 設定 |
| UC-ATWK 3.1.1.2 | 建立資料庫 | 建立 db_atwk 與所有 atwk_ 資料表 |
| UC-ATWK 3.1.1.3 | 設定 LLM 連線 | LiteLLM 配置，.env 填寫 |
| UC-ATWK 3.1.1.4 | 建立 wiki 目錄 | inbox/raw/wiki/templates 目錄初始化 |
| UC-ATWK 3.1.1.5 | FastAPI 骨架 | app 啟動，port 8300，/health 端點 |

### UC-ATWK 3.2 — WEB 前台

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.2.1.1 | 自然語言查詢 | 輸入框 → LLM 查詢 wiki → 回答 + 來源連結 |
| UC-ATWK 3.2.2.1 | Wiki 瀏覽 | 階層式目錄 + 頁面 Markdown 渲染 |
| UC-ATWK 3.2.3.1 | 教學說明 | 系統使用說明步驟頁 |

### UC-ATWK 3.3 — API

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.3.1.1 | Query API | POST /api/query → LLM 查詢 wiki 回答 |
| UC-ATWK 3.3.2.1 | Check-in API | GET /api/checkin → 回報服務健康狀態 |
| UC-ATWK 3.3.3.1 | Health API | GET /health → 基本健康檢查 |

### UC-ATWK 3.4 — Backend 後台管理

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.4.1.1 | 後台登入 | Token 驗證（Bearer Token） |
| UC-ATWK 3.4.2.1 | 文件上架 | 上傳文件至 inbox/ |
| UC-ATWK 3.4.2.2 | 文件列表 | raw/ + inbox/ 文件清單 |
| UC-ATWK 3.4.2.3 | 文件刪除 | 移除 inbox/ 文件 |
| UC-ATWK 3.4.3.1 | Ingest 歷程列表 | atwk_ingest_log 查詢（含分頁） |
| UC-ATWK 3.4.3.2 | 手動觸發 Ingest | 指定文件觸發 Ingest JOB |
| UC-ATWK 3.4.3.3 | Ingest 明細 | 單次 Ingest 產出的 wiki 頁面清單 |
| UC-ATWK 3.4.4.1 | Wiki 頁面列表 | atwk_wiki_page 清單查詢（含搜尋） |
| UC-ATWK 3.4.4.2 | Wiki 頁面檢視 | 頁面 Markdown 內容展示 |
| UC-ATWK 3.4.4.3 | Wiki 頁面刪除 | 軟刪除（is_delete = 'Y'）+ 刪除 md 檔 |
| UC-ATWK 3.4.4.4 | 手動觸發 Lint | 對指定頁面或全庫執行 Lint |

### UC-ATWK 3.5 — JOB 排程

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.5.1.1 | LLM Ingest（核心） | 原始文件 → LLM 分析 → wiki 頁面產出 |
| UC-ATWK 3.5.1.2 | 寫入 Ingest log | 每次 Ingest 寫入 atwk_ingest_log |
| UC-ATWK 3.5.1.3 | 更新 wiki 索引 | wiki/log.md + wiki/index.md 同步更新 |
| UC-ATWK 3.5.2.1 | inbox/ 自動偵測 | APScheduler 每 5 分鐘掃描 inbox/ |
| UC-ATWK 3.5.2.2 | 定期 Lint | APScheduler 每日執行 wiki Lint |
| UC-ATWK 3.5.2.3 | JOB 執行記錄 | atwk_job_log 記錄每次 JOB 結果 |

### UC-ATWK 3.6 — 異質系統

| UC 編號 | 功能名稱 | 說明 |
|---------|---------|------|
| UC-ATWK 3.6.1.1 | AgentPULSE Heartbeat | 定期向 APMS 打卡，回報健康狀態 |

---

## 3. 資料表設計

### atwk_document（文件索引）

| 欄位 | 型別 | 說明 |
|------|------|------|
| document_id | SERIAL PK | |
| file_name | VARCHAR(500) | 原始檔案名稱 |
| file_path | TEXT | 儲存路徑（raw/） |
| file_type | VARCHAR(50) | pptx/docx/pdf/txt |
| file_size | BIGINT | bytes |
| ingest_status | CHAR(1) | P=Pending, R=Running, D=Done, E=Error |
| *標準 8 欄* | | |

### atwk_ingest_log（Ingest 記錄）

| 欄位 | 型別 | 說明 |
|------|------|------|
| ingest_id | SERIAL PK | |
| document_id | INT FK | 對應文件 |
| ingest_start | TIMESTAMP | 開始時間 |
| ingest_end | TIMESTAMP | 結束時間 |
| status | CHAR(1) | S=Success, E=Error |
| page_count | INT | 產出 wiki 頁面數 |
| error_msg | TEXT | 錯誤訊息 |
| *create_* 四欄* | | 純 log 表 |

### atwk_wiki_page（Wiki 頁面索引）

| 欄位 | 型別 | 說明 |
|------|------|------|
| page_id | SERIAL PK | |
| page_path | VARCHAR(500) | wiki/ 下的相對路徑 |
| page_title | VARCHAR(500) | 頁面標題 |
| page_category | VARCHAR(100) | concepts/operations/architecture/sources/syntheses |
| source_document_id | INT FK | 來源文件 |
| ingest_id | INT FK | 產出的 Ingest 批次 |
| last_lint_date | TIMESTAMP | 最後 Lint 時間 |
| *標準 8 欄* | | |

### atwk_job_log（JOB 執行記錄）

| 欄位 | 型別 | 說明 |
|------|------|------|
| job_log_id | SERIAL PK | |
| job_name | VARCHAR(100) | inbox_scan/ingest/lint/heartbeat |
| start_time | TIMESTAMP | |
| end_time | TIMESTAMP | |
| status | CHAR(1) | S=Success, E=Error |
| result_msg | TEXT | |
| *create_* 四欄* | | 純 log 表 |

---

## 4. API 端點規劃

| 方法 | 路徑 | 說明 | Layer |
|------|------|------|-------|
| GET | /health | 健康檢查 | 1 |
| POST | /api/query | 自然語言查詢 | 2 |
| GET | /api/checkin | 打卡回報 | 6 |
| POST | /admin/login | 後台登入 | 3 |
| POST | /admin/documents/upload | 上傳文件 | 3 |
| GET | /admin/documents | 文件列表 | 3 |
| DELETE | /admin/documents/{id} | 文件刪除 | 3 |
| GET | /admin/ingest-logs | Ingest 歷程 | 3 |
| POST | /admin/ingest-logs/{doc_id}/trigger | 手動觸發 | 3 |
| GET | /admin/ingest-logs/{id}/detail | Ingest 明細 | 3 |
| GET | /admin/wiki-pages | Wiki 頁面列表 | 3 |
| GET | /admin/wiki-pages/{id} | Wiki 頁面內容 | 3 |
| DELETE | /admin/wiki-pages/{id} | Wiki 頁面刪除 | 3 |
| POST | /admin/wiki-pages/lint | 觸發 Lint | 3 |

---

## 5. 系統依賴

```
ATWK (8300)
  ├── PostgreSQL: db_atwk
  ├── LiteLLM (外部 LLM API)
  └── AgentPULSE APMS (打卡，Layer 6)
```
