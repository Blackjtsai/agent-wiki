# Portal 定期排程 JOB 說明

## 摘要

Portal 系統共有 15 個定期排程 JOB，負責頁面狀態自動流轉、資料清理、帳號管理與監控告警。

## JOB 清單

| JOB | UC | 功能 | 資料表 |
|-----|----|------|--------|
| JOB 01 | — | 審核通過（status=4）比對啟用時間後更新為上架（status=5） | portal_website_page |
| JOB 02 | — | status=5 且目前日期已失效，更新為 9（自動失效） | portal_website_page |
| JOB 03 | — | 刪除大於 5 個版本的頁面 NAS 資料 | portal_website_page |
| JOB 04 | — | 活動頁面審核通過（status=4）比對啟用時間後更新為上架（status=5） | portal_website_event |
| JOB 05 | — | 活動頁面 status=5 且目前日期已失效，更新為 9 | portal_website_event |
| JOB 06 | — | 直接刪除已失效且大於 60 天的活動頁面 | portal_website_event |
| JOB 07 | — | 移除已刪除且大於 90 天的文件檔案資料 | portal_upload_file |
| JOB 08 | — | 註記刪除 90 天未登入系統的帳號 | — |
| JOB 09 | — | 發送訊息（單筆發送）；僅重送 24hr 內訊息；24hr 以上更新 status=9 並發告警 | portal_send_message |
| JOB 10 | UC 3.5.10 | 發送活動留資清單給 PM | portal_event_data |
| JOB 11 | UC 3.5.11 | NAS housekeeping（清除 NAS 上的無效檔案或資料） | — |
| JOB 12 | UC 3.5.12 | 每日將有效帳號與 SSO 確認是否有效，無效自動刪除 | — |
| JOB 13 | UC 3.5.13 | 80 天無登入或已開帳號日的為主，自動 M+ 通知將刪除帳號 | — |
| JOB 14 | UC 3.5.14 | 自動檢測機制 | portal_system_check / portal_system_check_report / portal_system_check_report_detail |
| JOB 15 | UC 3.5.15 | 自動清除 job_log 執行紀錄 | portal_jo_log |

## JOB 09 特別說明

- 訊息列表需加上時間才顯示
- 只重送 24hr 內訊息；24hr 以上更新 status=9，呼叫 UC 3.3.19 發告警
- 每次操作更新 IP / USER / TIME
- 寄送失敗（回應碼 ≠ 0000）錯誤要寫入 status note
- 每小時 JOB：NAS 容量大於 20G 發告警（呼叫 UC 3.3.19）

## JOB 04 / 05 狀態流轉補充

每次更新同時需新增一筆 `portal_page_log` 歷程資料：
```sql
INSERT INTO portal_page_log (
  website_id = 'event',
  website_page_version = 0,
  website_page_code = $website_event_page_code,
  create_user = portal_job_id + ":" + portal_job_log_id
)
```

## 相關概念

- [[concepts/portal-page-status]]
- [[concepts/portal-event-status]]
- [[operations/portal-monitoring]]

## 來源

- [[sources/Portal_20260209]]

## 最後更新

2026-06-28
