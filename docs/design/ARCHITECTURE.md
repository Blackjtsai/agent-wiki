# ATWK — 系統架構圖（ARCHITECTURE.md）

> 實作新模組前，必須先更新本圖。

---

## 系統架構（Mermaid）

```mermaid
graph TD
    subgraph 使用者端
        U1[前台使用者<br/>自然語言查詢]
        U2[後台管理員<br/>文件上架 / 管理]
    end

    subgraph ATWK 服務 Port:8300
        FE[前台 WEB<br/>Vue 3 CDN]
        BE[後台管理 WEB<br/>Vue 3 CDN]

        subgraph FastAPI
            R_HEALTH[GET /health]
            R_QUERY[POST /api/query]
            R_CHECKIN[GET /api/checkin]
            R_ADMIN[/admin/* 後台 API]
        end

        subgraph JOB_APScheduler[APScheduler]
            JOB_SCAN[inbox_scan<br/>每5分鐘]
            JOB_INGEST[LLM Ingest]
            JOB_LINT[Lint<br/>每日]
            JOB_HB[Heartbeat<br/>定期]
        end

        subgraph Wiki知識庫
            INBOX[inbox/]
            RAW[raw/]
            WIKI[wiki/]
        end
    end

    subgraph 外部系統
        LLM[LiteLLM<br/>LLM API]
        PG[(PostgreSQL<br/>db_atwk)]
        APMS[AgentPULSE<br/>APMS]
    end

    U1 --> FE
    U2 --> BE
    FE --> R_QUERY
    BE --> R_ADMIN
    R_QUERY --> LLM
    R_QUERY --> WIKI
    R_ADMIN --> PG
    R_ADMIN --> INBOX
    JOB_SCAN --> INBOX
    JOB_SCAN --> JOB_INGEST
    JOB_INGEST --> LLM
    JOB_INGEST --> RAW
    JOB_INGEST --> WIKI
    JOB_INGEST --> PG
    JOB_LINT --> WIKI
    JOB_LINT --> LLM
    JOB_HB --> APMS
    R_CHECKIN --> APMS
```

---

## 資料流說明

### Ingest 流程

```
inbox/ 有新檔 → JOB_SCAN 偵測
  → 移檔到 raw/
  → LLM 分析原始文件
  → 產出 wiki/ 頁面（md 檔）
  → 寫入 atwk_wiki_page
  → 寫入 atwk_ingest_log
  → 更新 wiki/log.md + wiki/index.md
```

### Query 流程

```
使用者輸入問題
  → POST /api/query
  → 讀取 wiki/index.md 定位相關頁
  → 讀取相關 wiki/*.md
  → LLM 綜合回答
  → 回傳 answer + sources[]
```

### Heartbeat 流程

```
APScheduler 定期觸發
  → 收集服務健康資訊（DB 連線 / wiki 頁數 / 最後 Ingest 時間）
  → POST 到 APMS /checkin
  → 寫入 atwk_job_log
```

---

## 模組對應

| 模組 | 資料夾 | Port/Path |
|------|--------|-----------|
| FastAPI 主服務 | api/ | :8300 |
| 前台 WEB | frontend/ | /index.html |
| 後台管理 | backend/ | /admin.html |
| JOB 排程 | job/ | — |
| 異質系統 | external/ | — |
| DB migration | db/ | — |
