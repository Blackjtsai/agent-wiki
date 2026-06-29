# Portal 後台管理系統模組總覽

## 摘要

Portal 後台管理系統分為四大區塊：系統管理、網站基礎設定、網頁管理、共用管理機制，各模組對應一張或多張資料庫表格。

## 模組架構

### 系統管理
| 功能 | 資料表 |
|------|--------|
| 帳號管理 | portal_empy |
| 後台目錄管理 | portal_program_module |
| 帳號目錄管理 | portal_program |
| CD基本設定檔 | portal_definition |
| 維運單位管理 | portal_page_dept |
| 帳號登入紀錄 | portal_empy_login |
| 資料庫可視化 | — |
| 系統檢測主檔 | portal_system_check |
| 系統檢測報表 | portal_system_check_report |
| 系統檢測報表明細 | portal_system_check_report_detail |

### 網站基礎設定
| 功能 | 資料表 |
|------|--------|
| Template 管理 | portal_template |
| 網站基本資料 | portal_website |
| 元件管理 | portal_item / portal_item_attribute |

### 網頁管理
| 功能 | 資料表 |
|------|--------|
| 網站選單管理 | portal_menu |
| 網站頁面管理 | portal_website_page / portal_website_page_item / portal_website_page_item_data |
| 活動頁面管理 | portal_website_event |

### 共用管理機制
| 功能 | 資料表 |
|------|--------|
| 文件類型管理 | portal_upload_file_type |
| 文件資料管理 | portal_upload_file |
| 貼標管理 | portal_hashtag |
| 最新消息管理 | portal_news |
| 文章資料管理 | portal_article |
| 訊息發送資料 | portal_send_message |
| 活動資訊管理 | portal_event |
| 活動留資表單設定 | portal_event_data |
| 活動留資資料管理 | portal_event_data |

## 共用 CRUD 操作

大多數模組支援：新增 / 列表 / 查詢 / 刪除（在內容修改頁才出現）

## 相關概念

- [[concepts/portal-page-status]]
- [[concepts/portal-event-status]]
- [[operations/portal-jobs]]

## 來源

- [[sources/Portal_20260209]]

## 最後更新

2026-06-28
