# job/ — 工作藍圖

## 職責

APScheduler 排程模組。負責 inbox 監控、LLM Ingest、Wiki Lint、AgentPULSE Heartbeat。

## 預期目錄結構

```
job/
├── blueprint.md
├── scheduler.py            # APScheduler 初始化，掛載所有 JOB
├── inbox_scan.py           # JOB：inbox/ 自動偵測（每 5 分鐘）
├── ingest.py               # JOB：LLM Ingest 核心邏輯
├── lint.py                 # JOB：Wiki Lint（每日）
└── heartbeat.py            # JOB：AgentPULSE 打卡
```

## JOB 清單

| JOB | 檔案 | 頻率 | UC |
|-----|------|------|-----|
| inbox_scan | inbox_scan.py | 每 5 分鐘 | UC-ATWK 3.5.2.1 |
| ingest | ingest.py | 由 inbox_scan 觸發 / 手動觸發 | UC-ATWK 3.5.1.1 |
| lint | lint.py | 每日 00:00 | UC-ATWK 3.5.2.2 |
| heartbeat | heartbeat.py | 每 10 分鐘 | UC-ATWK 3.6.1.1 |

## Ingest 流程（ingest.py 核心）

```
1. 接收文件路徑
2. 根據副檔名選擇解析策略（pptx/docx/pdf/txt）
3. 呼叫 LiteLLM → 分析文件 → 產出 wiki 頁面草稿
4. 寫入 wiki/{category}/{slug}.md
5. 寫入 atwk_wiki_page（DB 索引）
6. 更新 wiki/index.md
7. 寫入 wiki/log.md
8. 寫入 atwk_ingest_log（結果 + 頁數）
```

## 實作順序

- Layer 2：ingest.py（核心 Ingest 邏輯）
- Layer 5：scheduler.py + inbox_scan.py + lint.py（完整排程）
- Layer 6：heartbeat.py（AgentPULSE 整合）

## 關鍵約束

- Ingest 失敗必須寫 atwk_ingest_log（status='E'），不得靜默失敗
- raw/ 內文件不可刪除或修改（只讀）
- 每次 JOB 執行都寫 atwk_job_log
