# agent-wiki — LLM Wiki 操作規範

## 這是什麼

`agent-wiki` 是以 Karpathy LLM Wiki 方法論為基礎的部門知識庫。
原始文件存放在 `raw/`，由 LLM 整理後維護在 `wiki/`，本檔案定義 LLM 的操作規範。

## 三層架構

```
raw/        原始來源層 — 規格書、SOP、PDF、文章等。來源真相，LLM 不得修改。
wiki/       知識層 — 由 LLM 整理與維護的結構化頁面，含摘要與交叉連結。
CLAUDE.md   規範層 — 定義 LLM 如何維護此 Wiki。
```

## 目錄結構

```
agent-wiki/
├─ CLAUDE.md              # 本規範檔
├─ raw/                   # 原始來源（不修改）
│  └─ assets/             # 圖片、附件
├─ templates/             # wiki 頁面模板
└─ wiki/
   ├─ concepts/           # 核心概念頁
   ├─ operations/         # 操作流程頁（API、SOP 步驟）
   ├─ sources/            # raw 來源的摘要 metadata 頁
   ├─ syntheses/          # 跨來源綜合分析、query file-back
   ├─ architecture/       # 系統架構頁
   ├─ index.md            # Wiki 導覽入口（回答問題前優先讀取）
   ├─ log.md              # 操作日誌（ingest/query/lint 紀錄）
   └─ overview.md         # 知識庫總覽
```

## 三種操作

### Ingest（匯入）
當 `raw/` 有新文件時執行：
1. 讀取來源，理解主題與內容
2. 在 `wiki/sources/` 建立來源摘要頁（含原始檔名、日期、主題、摘要）
3. 在對應的 `wiki/concepts/`、`wiki/operations/`、`wiki/architecture/` 更新或新增概念頁
4. 更新 `wiki/index.md` 新增或修訂索引條目
5. 在 `wiki/log.md` 追加 ingest 紀錄

### Query（查詢）
回答問題時：
1. 先讀 `wiki/index.md` 確定相關頁面
2. 讀取相關 wiki 頁面
3. 根據 wiki 內容回答（不直接回原始 raw）
4. 若答案有長期價值，回寫至 `wiki/syntheses/`

### Lint（維護）
定期或被要求時執行：
1. 檢查頁面是否有矛盾或過期資訊
2. 找出孤立頁（沒有被 index 引用的頁）
3. 確認 `index.md` 沒有遺漏頁面
4. 確認 `log.md` 有記錄最近操作
5. 提出修正建議（不自動修改，由人確認）

## 重要原則

- `raw/` 是原始證據，**LLM 不得修改 raw/ 內的任何檔案**
- wiki 頁面使用 `[[wikilinks]]` 格式建立交叉連結
- 每次 ingest 不只是摘要，而是**整合進既有知識結構**
- `index.md` 保持簡潔（頁面名稱 + 一句話摘要 + 分類）
- `log.md` 每次操作都要追加紀錄，格式：`YYYY-MM-DD | 操作類型 | 說明`
