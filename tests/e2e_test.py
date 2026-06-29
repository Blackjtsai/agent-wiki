# ============================================================
# File: e2e_test.py
# Desc: Layer 7 end-to-end integration tests
# Module: tests/
# Created: 2026-06-28
# Dev: Blackjtsai
#
# Usage:
#   uv run python tests/e2e_test.py
#
# Prerequisites:
#   - uvicorn running on port 8300
#   - db_atwk initialized (migration_001_init.sql executed)
#   - .env configured (DB + LLM)
# ============================================================

import asyncio
import sys
import time
import httpx

BASE = "http://localhost:8300"
ADMIN_TOKEN = None  # loaded from .env


def load_token() -> str:
    """Load ATWK_SECRET_KEY from .env."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    return os.getenv("ATWK_SECRET_KEY", "change-me-in-production")


def ok(label: str) -> None:
    print(f"  ✅ {label}")


def fail(label: str, detail: str = "") -> None:
    print(f"  ❌ {label}" + (f" — {detail}" if detail else ""))


# ══════════════════════════════════════════════════════════════
# Test Cases
# ══════════════════════════════════════════════════════════════

def test_health(client: httpx.Client) -> bool:
    print("\n[1] GET /health")
    try:
        r = client.get(f"{BASE}/health")
        assert r.status_code == 200, f"status={r.status_code}"
        data = r.json()
        assert data["status"] == "ok",   f"status={data['status']}"
        assert data["service"] == "ATWK", f"service={data['service']}"
        assert data["db"] == "ok",       f"db={data['db']}"
        ok("health 回傳正常")
        return True
    except Exception as e:
        fail("health 失敗", str(e))
        return False


def test_admin_login(client: httpx.Client, token: str) -> bool:
    print("\n[2] POST /admin/login")
    try:
        r = client.post(f"{BASE}/admin/login", json={"token": token})
        assert r.status_code == 200
        assert r.json()["success"] is True
        ok("登入成功")

        r2 = client.post(f"{BASE}/admin/login", json={"token": "wrong"})
        assert r2.status_code == 401
        ok("錯誤 token 回傳 401")
        return True
    except Exception as e:
        fail("登入測試失敗", str(e))
        return False


def test_document_upload(client: httpx.Client, token: str) -> int | None:
    """上傳一個測試用 txt 文件，回傳 document_id。"""
    print("\n[3] POST /admin/documents/upload")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        content = b"# Test Document\n\nThis is a test document for ATWK e2e testing.\n\nSection 1: Overview\nATWK is an intelligent wiki system.\n\nSection 2: Features\n- Auto ingest\n- Natural language query\n- Wiki management"
        files = {"file": ("e2e_test.txt", content, "text/plain")}
        r = client.post(f"{BASE}/admin/documents/upload", headers=headers, files=files)
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"
        data = r.json()
        doc_id = data["document_id"]
        ok(f"上傳成功 document_id={doc_id}")

        # 不支援格式應回 400
        bad = {"file": ("bad.xyz", b"content", "application/octet-stream")}
        r2 = client.post(f"{BASE}/admin/documents/upload", headers=headers, files=bad)
        assert r2.status_code == 400
        ok("不支援格式回傳 400")
        return doc_id
    except Exception as e:
        fail("上傳失敗", str(e))
        return None


def test_document_list(client: httpx.Client, token: str, doc_id: int) -> bool:
    print("\n[4] GET /admin/documents")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = client.get(f"{BASE}/admin/documents", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        ids = [d["document_id"] for d in data["items"]]
        assert doc_id in ids, f"doc_id={doc_id} not in list"
        ok(f"文件列表正常，共 {data['total']} 筆")
        return True
    except Exception as e:
        fail("文件列表失敗", str(e))
        return False


def test_ingest_trigger(client: httpx.Client, token: str, doc_id: int) -> bool:
    print("\n[5] POST /admin/ingest-logs/{doc_id}/trigger")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = client.post(f"{BASE}/admin/ingest-logs/{doc_id}/trigger", headers=headers)
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"
        ok(f"Ingest 觸發成功：{r.json()['message']}")

        # 等待背景 Ingest 完成（最多 30 秒）
        print("  ⏳ 等待 Ingest 完成（最多 30 秒）…")
        for _ in range(30):
            time.sleep(1)
            r2 = client.get(f"{BASE}/admin/documents?status=D", headers=headers)
            done_ids = [d["document_id"] for d in r2.json().get("items", [])]
            if doc_id in done_ids:
                ok("Ingest 完成（status=D）")
                return True

        # 若未完成，查是否有 log
        r3 = client.get(f"{BASE}/admin/ingest-logs", headers=headers)
        items = r3.json().get("items", [])
        for item in items:
            if item["document_id"] == doc_id:
                ok(f"Ingest log 存在（status={item['status']}）")
                return True

        fail("Ingest 未在 30 秒內完成")
        return False
    except Exception as e:
        fail("Ingest 觸發失敗", str(e))
        return False


def test_ingest_logs(client: httpx.Client, token: str) -> bool:
    print("\n[6] GET /admin/ingest-logs")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = client.get(f"{BASE}/admin/ingest-logs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        ok(f"Ingest 歷程列表正常，共 {data['total']} 筆")
        return True
    except Exception as e:
        fail("Ingest 歷程失敗", str(e))
        return False


def test_wiki_pages(client: httpx.Client, token: str) -> bool:
    print("\n[7] GET /api/wiki-pages (public)")
    try:
        r = client.get(f"{BASE}/api/wiki-pages")
        assert r.status_code == 200
        data = r.json()
        total = data.get("total", 0)
        ok(f"Wiki 頁面目錄正常，共 {total} 頁")

        if total > 0:
            # 取第一個頁面測試內容讀取
            for cat in ["concepts", "operations", "architecture", "sources", "syntheses"]:
                pages = data.get(cat, [])
                if pages:
                    page_id = pages[0]["page_id"]
                    r2 = client.get(f"{BASE}/api/wiki-pages/{page_id}")
                    assert r2.status_code == 200
                    content = r2.json().get("content", "")
                    assert len(content) > 0
                    ok(f"Wiki 頁面內容讀取正常（page_id={page_id}）")
                    break
        return True
    except Exception as e:
        fail("Wiki 頁面測試失敗", str(e))
        return False


def test_query(client: httpx.Client) -> bool:
    print("\n[8] POST /api/query")
    try:
        r = client.post(
            f"{BASE}/api/query",
            json={"q": "ATWK 系統有哪些功能？"},
            timeout=60.0,
        )
        assert r.status_code == 200, f"status={r.status_code}"
        data = r.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        ok(f"Query 回答正常（{len(data['answer'])} 字）")

        # Error path: 空字串
        r2 = client.post(f"{BASE}/api/query", json={"q": ""})
        assert r2.status_code == 422  # Pydantic min_length validation
        ok("空字串查詢回傳 422")
        return True
    except Exception as e:
        fail("Query 測試失敗", str(e))
        return False


def test_checkin(client: httpx.Client) -> bool:
    print("\n[9] GET /api/checkin")
    try:
        r = client.get(f"{BASE}/api/checkin")
        assert r.status_code == 200
        data = r.json()
        assert data["agent"] == "ATWK"
        assert data["status"] in ("ok", "warning", "error")
        assert "detail" in data
        ok(f"Check-in 正常（status={data['status']}, wiki_pages={data['detail'].get('wiki_page_count')}）")
        return True
    except Exception as e:
        fail("Check-in 失敗", str(e))
        return False


def test_scheduler_status(client: httpx.Client, token: str) -> bool:
    print("\n[10] GET /admin/scheduler/status")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = client.get(f"{BASE}/admin/scheduler/status", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["running"] is True
        job_ids = [j["id"] for j in data["jobs"]]
        for jid in ("inbox_scan", "daily_lint", "heartbeat"):
            assert jid in job_ids, f"JOB {jid} not found"
        ok(f"排程器正在執行，JOBs: {job_ids}")
        return True
    except Exception as e:
        fail("排程狀態失敗", str(e))
        return False


def test_auth_guard(client: httpx.Client) -> bool:
    print("\n[11] Auth guard — 未授權存取後台應回 401")
    try:
        for path in ["/admin/documents", "/admin/ingest-logs", "/admin/wiki-pages", "/admin/job-logs"]:
            r = client.get(f"{BASE}{path}")
            assert r.status_code == 401, f"{path} 回傳 {r.status_code}，預期 401"
        ok("所有後台路徑未授權均回傳 401")
        return True
    except Exception as e:
        fail("Auth guard 測試失敗", str(e))
        return False


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main() -> None:
    token = load_token()
    print("=" * 60)
    print("  ATWK Layer 7 端對端測試")
    print(f"  Target: {BASE}")
    print("=" * 60)

    results: list[bool] = []

    with httpx.Client(timeout=30.0) as client:
        # 1. Health
        results.append(test_health(client))
        if not results[-1]:
            print("\n⚠️  服務未啟動，終止測試。請先執行 uvicorn。")
            sys.exit(1)

        # 2. Auth
        results.append(test_admin_login(client, token))
        results.append(test_auth_guard(client))

        # 3. Document flow
        doc_id = test_document_upload(client, token)
        results.append(doc_id is not None)

        if doc_id:
            results.append(test_document_list(client, token, doc_id))
            results.append(test_ingest_trigger(client, token, doc_id))
            results.append(test_ingest_logs(client, token))

        # 4. Wiki & Query
        results.append(test_wiki_pages(client, token))
        results.append(test_query(client))

        # 5. Check-in & Scheduler
        results.append(test_checkin(client))
        results.append(test_scheduler_status(client, token))

    # Summary
    passed = sum(results)
    total  = len(results)
    print("\n" + "=" * 60)
    print(f"  結果：{passed}/{total} 通過")
    if passed == total:
        print("  🎉 所有測試通過！Layer 7 驗收完成。")
    else:
        print("  ⚠️  部分測試失敗，請查看上方錯誤訊息。")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
