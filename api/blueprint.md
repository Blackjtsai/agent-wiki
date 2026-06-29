# api/ — 工作藍圖

## 職責

FastAPI 主應用程式。提供 HTTP 端點，協調前後台請求、呼叫 LLM、讀寫 DB 與 wiki 目錄。

## 預期目錄結構

```
api/
├── main.py                  # FastAPI app 入口，掛載所有 router
├── config.py                # 讀取 .env，統一設定物件
├── database.py              # asyncpg 連線池
├── dependencies.py          # 共用 Depends（auth token 驗證等）
└── routers/
    ├── health.py            # GET /health
    ├── query.py             # POST /api/query（UC-ATWK 3.3.1.1）
    ├── checkin.py           # GET /api/checkin（UC-ATWK 3.3.2.1）
    ├── admin_auth.py        # POST /admin/login（UC-ATWK 3.4.1.1）
    ├── admin_documents.py   # /admin/documents/* （UC-ATWK 3.4.2.x）
    ├── admin_ingest.py      # /admin/ingest-logs/* （UC-ATWK 3.4.3.x）
    └── admin_wiki.py        # /admin/wiki-pages/* （UC-ATWK 3.4.4.x）
```

## 實作順序

1. main.py + config.py + database.py（Layer 1）
2. health.py（Layer 1）
3. query.py（Layer 2）
4. admin_auth.py + admin_documents.py + admin_ingest.py + admin_wiki.py（Layer 3）
5. checkin.py（Layer 6）

## 關鍵約束

- 所有 router 檔案加檔案 header 註解
- DB 操作使用 asyncpg（非 ORM）
- 後台 API 路徑統一前綴 `/admin/`，需驗證 Bearer Token
