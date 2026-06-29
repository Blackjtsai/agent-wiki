# /checkpoint — 對話結束前必執行

每次對話結束前，依序執行以下步驟：

## Step 1 — 更新 TODO.md

讀取 `docs/TODO.md`，將本次對話已完成的項目從 `[ ]` 改為 `[x]`。

## Step 2 — 確認 ARCHITECTURE.md

如果本次對話新增或修改了模組，確認 `docs/design/ARCHITECTURE.md` 的 Mermaid 架構圖已反映最新狀態。

## Step 3 — 更新 CHANGELOG.md

如果有實質功能完成（不只是規劃），在 `docs/CHANGELOG.md` 新增記錄：
```
## [版本] YYYY-MM-DD
### 新增 / 修改 / 修正
- 說明
```

## Step 4 — 更新 wiki/log.md

如果本次對話進行了 wiki 操作（Ingest / Lint / Query），在 `wiki/log.md` 新增記錄：
```
YYYY-MM-DD | 操作類型 | 說明
```

## Step 5 — 輸出對話摘要

以下格式輸出本次對話摘要，供下次對話開場使用：

```
## 本次對話摘要
- 完成事項：
- 進行中：
- 下次繼續：
- 注意事項：
```
