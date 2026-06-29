# ============================================================
# File: inbox_scan.py
# Desc: JOB - inbox/ folder scan, auto-trigger Ingest on new files
# Module: job/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

import shutil
from datetime import datetime, timezone
from pathlib import Path

from api.config import settings
from api.database import get_conn
from job.parsers import SUPPORTED_EXTENSIONS


async def run_inbox_scan() -> dict:
    """掃描 inbox/ 資料夾，對每個新文件觸發 Ingest。

    流程：
    1. 列出 inbox/ 下所有支援格式檔案
    2. 查 DB 確認是否已有 Pending/Running 記錄（避免重複）
    3. 對新檔案：移動至 raw/、建立 atwk_document 記錄、觸發 Ingest
    4. 寫入 atwk_job_log

    Returns:
        {"found": int, "triggered": int, "errors": list}
    """
    start_time = datetime.now(timezone.utc)
    job_log_id: int | None = None

    async with get_conn() as conn:
        job_log_id = await conn.fetchval(
            """
            INSERT INTO atwk_job_log (job_name, start_time, status, create_date)
            VALUES ('inbox_scan', $1, 'R', NOW())
            RETURNING job_log_id
            """,
            start_time,
        )

    inbox_path = Path(settings.inbox_dir)
    raw_path   = Path(settings.raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)

    # 找出所有支援格式的檔案（排除 .gitkeep）
    candidates = [
        f for f in inbox_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    found     = len(candidates)
    triggered = 0
    errors: list[str] = []

    for file in candidates:
        try:
            # 查 DB：是否已有同檔名的 Pending/Running/Done 記錄
            async with get_conn() as conn:
                existing = await conn.fetchval(
                    """
                    SELECT document_id FROM atwk_document
                    WHERE file_name = $1 AND ingest_status IN ('P','R','D') AND is_delete = 'N'
                    """,
                    file.name,
                )

            if existing:
                continue  # 已處理過，跳過

            # 移動至 raw/（若同名則加時間戳）
            dest = raw_path / file.name
            if dest.exists():
                ts   = datetime.now().strftime("%Y%m%d%H%M%S")
                dest = raw_path / f"{file.stem}_{ts}{file.suffix}"
            shutil.move(str(file), str(dest))

            # 建立 DB 記錄
            async with get_conn() as conn:
                doc_id = await conn.fetchval(
                    """
                    INSERT INTO atwk_document
                        (file_name, file_path, file_type, file_size, ingest_status, create_date)
                    VALUES ($1, $2, $3, $4, 'P', NOW())
                    RETURNING document_id
                    """,
                    dest.name,
                    str(dest),
                    dest.suffix.lower().lstrip("."),
                    dest.stat().st_size,
                )

            # 觸發 Ingest（非同步，不等待結果）
            from job.ingest import run_ingest
            import asyncio
            asyncio.create_task(
                run_ingest(document_id=doc_id, file_path=str(dest), file_name=dest.name)
            )
            triggered += 1

        except Exception as e:
            errors.append(f"{file.name}: {e}")

    # 更新 job_log
    result_msg = f"found={found}, triggered={triggered}"
    if errors:
        result_msg += f", errors={errors}"

    async with get_conn() as conn:
        await conn.execute(
            """
            UPDATE atwk_job_log
            SET status=$1, end_time=NOW(), result_msg=$2
            WHERE job_log_id=$3
            """,
            "S" if not errors else "E",
            result_msg,
            job_log_id,
        )

    return {"found": found, "triggered": triggered, "errors": errors}
