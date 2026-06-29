# backend/ — 工作藍圖

## 職責

後台管理 WEB 介面。提供管理員進行文件上架、Ingest 歷程查看、Wiki 頁面管理等操作。

## 技術選型

Vue 3（CDN 引入），單 HTML 檔案，Bearer Token 驗證。

## 預期目錄結構

```
backend/
├── blueprint.md
└── admin.html              # 後台主頁（含 Vue 3 CDN）
```

## 頁面規劃

### 登入頁

- 輸入 Token → 送出 `POST /admin/login` → 成功後跳轉後台主頁
- Token 存在 sessionStorage

### Tab 1 — 文件管理

- 顯示 inbox/ + raw/ 文件列表（檔名、大小、狀態、上傳時間）
- 「上傳文件」按鈕 → `POST /admin/documents/upload`（支援拖拉）
- 「刪除」按鈕 → `DELETE /admin/documents/{id}`
- 「立即 Ingest」按鈕 → `POST /admin/ingest-logs/{doc_id}/trigger`

### Tab 2 — Ingest 歷程

- 列表：時間、文件名、狀態（成功/失敗）、產出頁數
- 點擊展開明細 → 顯示產出的 wiki 頁面清單
- 支援分頁

### Tab 3 — Wiki 頁面管理

- 列表：頁面路徑、標題、分類、最後更新時間
- 搜尋框（按標題/分類過濾）
- 「檢視」→ Markdown 渲染 Modal
- 「刪除」→ 確認 Dialog → `DELETE /admin/wiki-pages/{id}`
- 「執行 Lint」按鈕 → `POST /admin/wiki-pages/lint`

### Tab 4 — JOB 執行記錄

- 顯示 atwk_job_log 記錄（job_name / 時間 / 狀態 / 結果）

## 實作順序（Layer 3）

1. admin.html 骨架（登入頁 + Tab 切換）
2. 文件管理 Tab + 上傳功能
3. Ingest 歷程 Tab
4. Wiki 頁面管理 Tab
5. JOB 執行記錄 Tab
