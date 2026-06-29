# 智能知識庫管理系統（ATWK）— 系統簡介

## 系統代號

ATWK

## 系統名稱

- 中文：智能知識庫管理系統
- 英文：Agent Wiki Knowledge Management System

## 系統目標

提供部門層級的 AI 知識庫，將各類原始文件（PowerPoint、Word、PDF、文字檔）透過 LLM 自動整理成結構化 Wiki 頁面，並以自然語言查詢介面對外提供知識服務。

作為獨立數位員工，完成後與 AgentHQ（ATHQ）生態整合，定期向 AgentPULSE（APMS）回報健康狀態。

## 核心功能

1. **自動 Ingest**：監控 `inbox/` 資料夾，有新文件時自動執行 LLM Ingest → 產生 Wiki 頁面
2. **前台查詢**：自然語言輸入，LLM 搜尋 Wiki 後回答，提供知識溯源連結
3. **後台管理**：文件上架、Ingest 歷程查看、Wiki 頁面管理、Lint 觸發
4. **教學說明**：產品使用教學，完整的步驟說明

## 相依系統

| 系統 | 代號 | 關係 |
|------|------|------|
| AgentPULSE | APMS | 數位員工定期打卡（Heartbeat） |
| AgentHQ | ATHQ | 未來作為 AgentHQ 內的 AI 員工對接 |

## 技術棧快照

Python 3.12 / FastAPI / asyncpg / PostgreSQL（db_atwk） / LiteLLM / Vue 3（CDN） / APScheduler / uv

## 對外服務 Port

8300

## 開發方法論

Tsai-Style OpenSpec SOP + new-project-init v1.4  
見 `D:\_claude-project\eason-skills\new-project-init.md`
