# Portal 監控機制

## 摘要

Portal 採用 ELK 進行日誌分析，並搭配自動監控 JOB（JOB 14）及後台系統檢測報表，主動偵測異常。

## 監控架構

### ELK
- **E**lasticsearch：日誌儲存與索引
- **L**ogstash：日誌收集與處理管道
- **K**ibana：視覺化儀錶板
- 部署於 INTRA 區

### API / Web 自動監控
- 透過 JOB 14（UC 3.5.14）定期執行系統自動檢測
- 結果記錄至：
  - `portal_system_check`（主檔）
  - `portal_system_check_report`（報表）
  - `portal_system_check_report_detail`（明細）
- 後台可查詢：系統管理 > 系統檢測報表，支援手動觸發檢測

### 告警機制
- 容量告警：NAS 容量 > 20G → 呼叫 UC 3.3.19 發 M+ 告警（每小時 JOB）
- 訊息發送失敗：24hr 以上未成功 → 呼叫 UC 3.3.19 發告警
- 帳號異常：SSO 無效帳號（JOB 12）、長期未登入（JOB 13）

## 相關 JOB

- [[operations/portal-jobs]] → JOB 09（訊息告警）、JOB 14（系統自動檢測）

## 相關概念

- [[architecture/portal-infra]]

## 來源

- [[sources/Portal_20260209]]

## 最後更新

2026-06-28
