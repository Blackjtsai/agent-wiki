# 智能知識庫管理系統（ATWK）— 專案規範 (CLAUDE.md)

---

# 一、通用規範

## Claude 行為規範（Karpathy Coding Guidelines）

- **Think Before Coding**：有假設或模糊地帶，先說出來對齊，不要默默實作
- **Simplicity First**：只寫解決當前問題最少的程式碼，不預留「未來可能用到」的抽象
- **Surgical Changes**：只動必要的地方，不順手重構周邊不相關的程式碼
- **Goal-Driven Execution**：每個任務完成前，先定義可驗證的成功標準，達到才繼續

## 不問已知規範

有合理預設答案時直接執行，不問。只有在真正有歧義且無法從上下文推斷時才提問。

## 文件資料夾管理規範

- `docs/design/` — 設計類（需求、SDD、架構等規劃文件）
- `docs/specs/` — 規格類（API 規格、服務說明書、流程圖等衍生文件）
- `docs/requirements/` — 需求來源（原始需求文件）
- **滾動式調整**：資料夾結構不清楚時，自動提醒使用者討論調整，不自行亂動

## 檔案異動盤查規範

資料夾或檔案位置變動時，主動盤查：Import 路徑、設定檔引用、CLAUDE.md 目錄結構區塊、測試路徑。
異動影響超過 1 個檔案時，先列受影響清單讓使用者確認，再動手。

## 自動記憶規範

- **錯誤經驗**：對話中發生錯誤或誤判，立即寫入專案 memory 目錄，類型 `feedback`
- **系統藍圖**：實作新模組前，必須先產出或更新 `ARCHITECTURE.md` 的 Mermaid 架構圖

## Todo 管理規範

- **唯一來源**：進度以 `docs/TODO.md` 為準
- 每個 Layer 開始前，先在 `docs/design/TASK.md` 列出驗收條件，再在 `docs/TODO.md` 展開細項，再動手
- **TASK.md gate**：`docs/TODO.md` 出現新 Layer，但 `docs/design/TASK.md` 無對應條目 → 停下來，先補寫 TASK.md
- 每完成一項，立即更新 `docs/TODO.md`（`[ ]` → `[x]`）
- 上一 Layer 所有項目 `[x]` 才能開新 Layer

## 專案開場問候規範

使用者輸入 `hi` 時，依序執行：

0. **環境檢查** — 讀取 `docs/SETUP.md`，逐項列出就緒 ✅ / 未完成 ❌
1. **打招呼** — 問候使用者
2. **專案任務說明** — 一段話說明此專案的目的與階段
3. **Claude 技能清單** — 列出目前可執行的任務，固定包含 `/checkpoint` 與 `/checkservice`
4. **目前進度** — 讀取 `docs/TODO.md`，對照 Layer 驗收表
5. **可對外服務** — 說明哪些端點 / 功能目前已可使用

## 程式碼註解規範

每支程式碼檔案都必須包含：

**1. 檔案 header（最頂端）**
```
# ============================================================
# 檔案名稱：xxx.py
# 中文名稱：（繁體中文說明）
# 功能說明：（一行說清楚此檔的職責）
# 所屬模組：（對應的模組或資料夾）
# 建立日期：YYYY-MM-DD
# 修改日期：YYYY-MM-DD
# 開發者　：Blackjtsai
# ============================================================
```

**2. 每個函式 / 方法的 docstring**

## 測試規範（Error Path）

1. 驗收條件必須列 error path 預期行為
2. 每個 `except XxxError`，加一個 sibling exception 測試
3. monkeypatch 前自問「我是在測這個值，還是繞過它？」

## 資料表設計規範

### 命名規則

- 資料表命名：`atwk_{業務實體名稱}`（全小寫、底線分隔）
- PK：`{業務實體名稱}_id`
- FK：`{被參照表業務實體名稱}_id`
- 代碼識別：`{業務實體名稱}_code`

### 標準 8 欄

每張主要業務資料表在業務欄位之後加入：

| 欄位 | 型別 | 預設 | 說明 |
|------|------|------|------|
| `note` | TEXT | — | 備註 |
| `is_delete` | CHAR(1) | `'N'` | 軟刪除 CHECK IN ('Y','N') |
| `create_user` | VARCHAR(100) | — | 建立人員 |
| `create_date` | TIMESTAMP | `NOW()` | 建立時間 |
| `create_ip` | VARCHAR(50) | — | 新增 IP |
| `update_user` | VARCHAR(100) | — | 更新人員 |
| `update_date` | TIMESTAMP | — | 異動時間 |
| `update_ip` | VARCHAR(50) | — | 異動 IP |

純 log 表：僅加 `create_*` 四欄。命名慣例：`create_date` / `update_date`。

---

# 二、業務邏輯規範

## 專案快照

**智能知識庫管理系統（ATWK）**
部門層級 AI 知識庫，文件 Ingest → LLM 整理 → Wiki 頁面，提供前台自然語言查詢與後台管理，作為獨立數位員工與 AgentHQ 生態整合。

參考文件：
- `docs/design/SDD.md` — 系統設計說明書
- `docs/design/TASK.md` — 各 Layer 驗收條件
- `wiki/WIKI-RULES.md` — Wiki 知識庫操作規範（LLM Ingest/Query/Lint 規則）

## 技術棧

| 層 | 技術 |
|----|------|
| 語言 | Python 3.12 |
| 框架 | FastAPI + asyncpg |
| 資料庫 | PostgreSQL（db_atwk） |
| LLM | LiteLLM |
| 前台 / 後台 UI | Vue 3（CDN，單 HTML 檔） |
| 排程 | APScheduler |
| 套件管理 | uv |
| Port | 8300 |

## 必備技能

- `/checkpoint` — **必備**，每次對話結束前執行
- `/checkservice` — 確認 PostgreSQL + uvicorn（port 8300）就緒

## 實作順序（嚴格遵守，未驗收不動下一層）

| Layer | 名稱 | UC 範圍 |
|-------|------|---------|
| Layer 1 | 資料層 + 環境建置 | UC-ATWK 3.1 |
| Layer 2 | API + Ingest 核心邏輯 | UC-ATWK 3.3.1 + 3.5.1 |
| Layer 3 | 後台管理 | UC-ATWK 3.4 |
| Layer 4 | 前台 WEB | UC-ATWK 3.2 |
| Layer 5 | JOB 排程完整化 | UC-ATWK 3.5.2 |
| Layer 6 | 異質系統整合 | UC-ATWK 3.6 + 3.3.2 |
| Layer 7 | 端對端整合測試 | 全 UC |

## 開發慣例

### UC 編號規範

格式：`UC-ATWK 3.{第一層}.{第二層}.{第三層}`

| 第一層 | 類別 |
|--------|------|
| 3.1 | 基礎建設（必含） |
| 3.2 | WEB 前台 |
| 3.3 | API |
| 3.4 | Backend 後台管理 |
| 3.5 | JOB 排程 |
| 3.6 | 異質系統 |

- UC 清單完整定義在 `docs/design/SDD.md` 的 `## UC 清單` 章節
- commit message 格式：`feat: UC-ATWK 3.x.x.x [功能名稱]`

### Wiki 知識庫目錄規範

- `inbox/` — 等待 Ingest 的原始文件（排程監控）
- `raw/` — 已 Ingest 的原始來源（不修改）
- `wiki/` — LLM 維護的知識頁面
- `templates/` — Wiki 頁面模板

### 其他命名慣例

- API router 檔案：`api/routers/{功能}.py`
- DB migration：`db/migration_{序號}_{說明}.sql`

## 關鍵業務約束

- `raw/` 內的檔案 LLM 不得修改
- Ingest 每次操作必須寫入 `atwk_ingest_log`
- Wiki 頁面同時維護 Markdown 檔案（`wiki/`）與 DB 索引（`atwk_wiki_page`）

## 專案目錄結構

```
agent-wiki/
├── CLAUDE.md                      # 專案規範（本檔）
├── .gitignore
├── .env                           # 環境變數（git 排除）
├── .env.example
├── pyproject.toml
├── inbox/                         # 等待 Ingest 的文件（排程監控）
├── raw/                           # 已 Ingest 的原始來源
│   └── assets/
├── wiki/                          # LLM 維護的知識頁面
│   ├── WIKI-RULES.md              # Wiki 操作規範
│   ├── index.md
│   ├── log.md
│   ├── overview.md
│   ├── concepts/
│   ├── operations/
│   ├── sources/
│   ├── syntheses/
│   └── architecture/
├── templates/                     # Wiki 頁面模板
├── api/                           # FastAPI 主應用
│   ├── blueprint.md
│   ├── main.py
│   └── routers/
├── frontend/                      # 前台 WEB
│   └── blueprint.md
├── backend/                       # 後台管理
│   └── blueprint.md
├── job/                           # 排程 JOB
│   └── blueprint.md
├── external/                      # 異質系統整合
│   └── blueprint.md
├── db/                            # DB migration scripts
└── docs/
    ├── INTRO.md
    ├── TODO.md
    ├── SETUP.md
    ├── CHANGELOG.md
    └── design/
        ├── ARCHITECTURE.md
        ├── TASK.md
        └── SDD.md
```
