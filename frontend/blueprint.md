# frontend/ — 工作藍圖

## 職責

前台 WEB 使用者介面。提供自然語言查詢、Wiki 瀏覽、教學說明三個主要頁面。

## 技術選型

Vue 3（CDN 引入，不需 build step），單 HTML 檔案。

## 預期目錄結構

```
frontend/
├── blueprint.md
└── index.html              # 前台主頁（含 Vue 3 CDN）
```

## 頁面規劃

### Tab 1 — 知識查詢

- 頂部搜尋框（輸入自然語言問題）
- 送出 → `POST /api/query` → 顯示 LLM 回答
- 回答下方顯示來源 wiki 頁面連結（可點擊跳至 Tab 2）
- Loading 狀態動畫

### Tab 2 — Wiki 瀏覽

- 左側：wiki 目錄樹（按 category 分群：architecture / concepts / operations / sources）
- 右側：選中頁面的 Markdown 內容（使用 marked.js 渲染）
- 支援 wikilinks 跳轉（[[page]] 格式）

### Tab 3 — 使用教學

- 步驟式說明（Step 1 上傳文件 → Step 2 等待 Ingest → Step 3 查詢知識）
- 配合截圖或圖示

## 實作順序（Layer 4）

1. index.html 骨架（三個 Tab，Vue 3 CDN）
2. 查詢 Tab + API 串接
3. Wiki 瀏覽 Tab（需額外 `GET /api/wiki-pages` API）
4. 教學說明 Tab（靜態內容）
