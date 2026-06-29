# Portal 系統環境架構

## 摘要

Portal 系統部署於 DMZ（前台）與 INTRA（後台 API + DB）之間，透過 L4 Load Balancer、防火牆（FW）、WAF 進行流量控管，並以 NAS 掛載共享資料空間。

## 架構示意

```
Internet
   │
  WAF
   │
  L4 / FW
   │
  DMZ ─────────────────────────────────────────
   │  前台網站服務（eservice.twmsolution.com）
   │  活動頁面、產品前台
   │
  INTRA ───────────────────────────────────────
   │  後台管理系統（eservice.backend.twmsolution.com）
   │  API（eservice.api.twmsolution.com）
   │  DB（PostgreSQL）
   │  ELK（日誌收集與分析）
   │  NAS（DATA 空間，BVM×2）
```

## 各層網址規則

| 環境 | 前台 | 後台 | API |
|------|------|------|-----|
| PRD | eservice.twmsolution.com | eservice.backend.twmsolution.com | eservice.api.twmsolution.com |
| UAT | uat-eservice.twmsolution.com | uat-eservice.backend.twmsolution.com | uat-eservice.api.twmsolution.com |
| SIT | sit-eservice.twmsolution.com | sit-eservice.backend.twmsolution.com | sit-eservice.api.twmsolution.com |

## 重要元件

- **WAF**：Web Application Firewall，最外層防護
- **L4/FW**：流量分發與防火牆
- **ELK**：Elasticsearch + Logstash + Kibana，日誌監控
- **NAS**：網路儲存裝置，OS 快照約十分鐘一次 / 可手動（SOP 五月確認）
- **PostgreSQL**：主資料庫

## 相關概念

- [[architecture/portal-environments]]
- [[operations/portal-monitoring]]

## 來源

- [[sources/Portal_20260209]]

## 最後更新

2026-06-28
