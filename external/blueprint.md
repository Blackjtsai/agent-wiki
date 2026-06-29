# external/ — 工作藍圖

## 職責

異質系統整合模組。目前唯一對接目標為 AgentPULSE（APMS），作為數位員工定期打卡。

## 預期目錄結構

```
external/
├── blueprint.md
└── agentpulse.py           # AgentPULSE 打卡客戶端
```

## agentpulse.py 介面

```python
async def send_heartbeat(status: str, detail: dict) -> bool:
    """
    向 AgentPULSE POST 打卡。
    status: "ok" | "warning" | "error"
    detail: {
        "db": "ok" | "error",
        "wiki_page_count": int,
        "last_ingest": "ISO datetime" | None
    }
    回傳 True = 打卡成功，False = 失敗（呼叫方寫 job_log）
    """
```

## APMS 端點（待 Layer 6 確認）

```
POST {APMS_BASE_URL}/agents/{APMS_AGENT_ID}/heartbeat
Body: {
    "agent_code": "ATWK",
    "status": "ok",
    "detail": {...}
}
```

## 實作順序（Layer 6）

1. agentpulse.py 客戶端實作
2. GET /api/checkin（api/routers/checkin.py）
3. job/heartbeat.py 串接 agentpulse.py
4. .env 填寫 APMS_BASE_URL + APMS_AGENT_ID
