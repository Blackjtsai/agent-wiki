-- ============================================================
-- ATWK migration_001_init.sql
-- 建立日期：2026-06-28
-- 說明：初始化所有資料表
-- 執行：psql -d db_atwk -f db/migration_001_init.sql
-- ============================================================

-- ============================================================
-- atwk_document — 文件索引
-- ============================================================
CREATE TABLE IF NOT EXISTS atwk_document (
    document_id   SERIAL          PRIMARY KEY,
    file_name     VARCHAR(500)    NOT NULL,
    file_path     TEXT            NOT NULL,
    file_type     VARCHAR(50)     NOT NULL,          -- pptx / docx / pdf / txt
    file_size     BIGINT          NOT NULL DEFAULT 0,
    ingest_status CHAR(1)         NOT NULL DEFAULT 'P'
                  CHECK (ingest_status IN ('P','R','D','E')),  -- Pending/Running/Done/Error
    -- 標準 8 欄
    note          TEXT,
    is_delete     CHAR(1)         NOT NULL DEFAULT 'N' CHECK (is_delete IN ('Y','N')),
    create_user   VARCHAR(100),
    create_date   TIMESTAMP       NOT NULL DEFAULT NOW(),
    create_ip     VARCHAR(50),
    update_user   VARCHAR(100),
    update_date   TIMESTAMP,
    update_ip     VARCHAR(50)
);

COMMENT ON TABLE  atwk_document                IS '文件索引';
COMMENT ON COLUMN atwk_document.document_id    IS '文件 PK';
COMMENT ON COLUMN atwk_document.file_name      IS '原始檔案名稱';
COMMENT ON COLUMN atwk_document.file_path      IS '儲存路徑（raw/ 下的相對路徑）';
COMMENT ON COLUMN atwk_document.file_type      IS '檔案類型 pptx/docx/pdf/txt';
COMMENT ON COLUMN atwk_document.file_size      IS '檔案大小（bytes）';
COMMENT ON COLUMN atwk_document.ingest_status  IS 'P=Pending R=Running D=Done E=Error';

-- ============================================================
-- atwk_ingest_log — Ingest 操作記錄（純 log 表）
-- ============================================================
CREATE TABLE IF NOT EXISTS atwk_ingest_log (
    ingest_id     SERIAL          PRIMARY KEY,
    document_id   INT             NOT NULL REFERENCES atwk_document(document_id),
    ingest_start  TIMESTAMP       NOT NULL DEFAULT NOW(),
    ingest_end    TIMESTAMP,
    status        CHAR(1)         NOT NULL DEFAULT 'R'
                  CHECK (status IN ('R','S','E')),   -- Running/Success/Error
    page_count    INT             NOT NULL DEFAULT 0,
    error_msg     TEXT,
    -- create_* 四欄（純 log 表）
    create_user   VARCHAR(100),
    create_date   TIMESTAMP       NOT NULL DEFAULT NOW(),
    create_ip     VARCHAR(50)
);

COMMENT ON TABLE  atwk_ingest_log              IS 'LLM Ingest 操作記錄';
COMMENT ON COLUMN atwk_ingest_log.ingest_id    IS 'Ingest 批次 PK';
COMMENT ON COLUMN atwk_ingest_log.document_id  IS '對應文件 FK';
COMMENT ON COLUMN atwk_ingest_log.status       IS 'R=Running S=Success E=Error';
COMMENT ON COLUMN atwk_ingest_log.page_count   IS '本批次產出 wiki 頁面數';

-- ============================================================
-- atwk_wiki_page — Wiki 頁面索引
-- ============================================================
CREATE TABLE IF NOT EXISTS atwk_wiki_page (
    page_id            SERIAL          PRIMARY KEY,
    page_path          VARCHAR(500)    NOT NULL UNIQUE,  -- wiki/ 下相對路徑
    page_title         VARCHAR(500)    NOT NULL,
    page_category      VARCHAR(100)    NOT NULL,         -- concepts/operations/architecture/sources/syntheses
    source_document_id INT             REFERENCES atwk_document(document_id),
    ingest_id          INT             REFERENCES atwk_ingest_log(ingest_id),
    last_lint_date     TIMESTAMP,
    -- 標準 8 欄
    note               TEXT,
    is_delete          CHAR(1)         NOT NULL DEFAULT 'N' CHECK (is_delete IN ('Y','N')),
    create_user        VARCHAR(100),
    create_date        TIMESTAMP       NOT NULL DEFAULT NOW(),
    create_ip          VARCHAR(50),
    update_user        VARCHAR(100),
    update_date        TIMESTAMP,
    update_ip          VARCHAR(50)
);

COMMENT ON TABLE  atwk_wiki_page                    IS 'Wiki 頁面索引';
COMMENT ON COLUMN atwk_wiki_page.page_id            IS '頁面 PK';
COMMENT ON COLUMN atwk_wiki_page.page_path          IS 'wiki/ 下相對路徑（唯一）';
COMMENT ON COLUMN atwk_wiki_page.page_title         IS '頁面標題';
COMMENT ON COLUMN atwk_wiki_page.page_category      IS 'concepts/operations/architecture/sources/syntheses';
COMMENT ON COLUMN atwk_wiki_page.source_document_id IS '來源文件 FK';
COMMENT ON COLUMN atwk_wiki_page.ingest_id          IS '產出此頁的 Ingest 批次 FK';
COMMENT ON COLUMN atwk_wiki_page.last_lint_date     IS '最後 Lint 時間';

-- ============================================================
-- atwk_job_log — JOB 執行記錄（純 log 表）
-- ============================================================
CREATE TABLE IF NOT EXISTS atwk_job_log (
    job_log_id  SERIAL          PRIMARY KEY,
    job_name    VARCHAR(100)    NOT NULL,   -- inbox_scan / ingest / lint / heartbeat
    start_time  TIMESTAMP       NOT NULL DEFAULT NOW(),
    end_time    TIMESTAMP,
    status      CHAR(1)         NOT NULL DEFAULT 'R'
                CHECK (status IN ('R','S','E')),
    result_msg  TEXT,
    -- create_* 四欄（純 log 表）
    create_user VARCHAR(100),
    create_date TIMESTAMP       NOT NULL DEFAULT NOW(),
    create_ip   VARCHAR(50)
);

COMMENT ON TABLE  atwk_job_log             IS 'APScheduler JOB 執行記錄';
COMMENT ON COLUMN atwk_job_log.job_log_id  IS 'JOB 記錄 PK';
COMMENT ON COLUMN atwk_job_log.job_name    IS 'inbox_scan/ingest/lint/heartbeat';
COMMENT ON COLUMN atwk_job_log.status      IS 'R=Running S=Success E=Error';

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_document_ingest_status ON atwk_document(ingest_status);
CREATE INDEX IF NOT EXISTS idx_document_is_delete     ON atwk_document(is_delete);
CREATE INDEX IF NOT EXISTS idx_ingest_log_document    ON atwk_ingest_log(document_id);
CREATE INDEX IF NOT EXISTS idx_ingest_log_status      ON atwk_ingest_log(status);
CREATE INDEX IF NOT EXISTS idx_wiki_page_category     ON atwk_wiki_page(page_category);
CREATE INDEX IF NOT EXISTS idx_wiki_page_is_delete    ON atwk_wiki_page(is_delete);
CREATE INDEX IF NOT EXISTS idx_job_log_job_name       ON atwk_job_log(job_name);
CREATE INDEX IF NOT EXISTS idx_job_log_start_time     ON atwk_job_log(start_time DESC);

-- ============================================================
-- 完成
-- ============================================================
SELECT 'migration_001_init.sql 執行完成' AS result;
