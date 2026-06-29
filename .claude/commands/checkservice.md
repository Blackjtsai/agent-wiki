# /checkservice — 確認服務就緒

執行以下檢查，逐項列出 ✅ / ❌：

## 1. PostgreSQL

```bash
pg_isready -h localhost -p 5432 -d db_atwk
```

預期：`localhost:5432 - accepting connections`

## 2. uvicorn (port 8300)

```bash
curl -s http://localhost:8300/health
```

預期：`{"status":"ok","service":"ATWK"}`

## 3. LLM 連線

呼叫 LiteLLM 簡單測試（echo prompt），確認回傳正常。

## 4. wiki 目錄

確認以下目錄存在：
- inbox/
- raw/
- wiki/
- templates/

## 輸出格式

```
## 服務檢查結果
- PostgreSQL db_atwk：✅ 正常 / ❌ 無法連線
- uvicorn :8300：✅ 正常 / ❌ 未啟動
- LLM 連線：✅ 正常 / ❌ 失敗（錯誤訊息）
- wiki 目錄：✅ 完整 / ❌ 缺少 {目錄名稱}
```
