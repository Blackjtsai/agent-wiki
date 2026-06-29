"""ATWK e2e test runner - uses Python directly (no bat env var issues)."""
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent

def read_env():
    env = {}
    env_path = ROOT / '.env'
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env

def log(msg):
    print(msg, flush=True)

async def setup_db(env):
    import asyncpg
    host = env.get('ATWK_DB_HOST', 'localhost')
    port = int(env.get('ATWK_DB_PORT', 5432))
    user = env.get('ATWK_DB_USER', 'postgres')
    password = env.get('ATWK_DB_PASSWORD', '')
    dbname = env.get('ATWK_DB_NAME', 'db_atwk')

    log(f"Connecting to postgres DB as {user} (password={'set' if password else 'empty'})...")
    try:
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database='postgres'
        )
    except Exception as e:
        log(f"ERROR connecting to postgres: {e}")
        log("Trying without password (trust auth)...")
        conn = await asyncpg.connect(
            host=host, port=port, user=user, database='postgres'
        )

    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", dbname)
    if not exists:
        await conn.execute(f'CREATE DATABASE "{dbname}"')
        log(f"  Created database {dbname}")
    else:
        log(f"  Database {dbname} already exists")
    await conn.close()

    log(f"Running migration on {dbname}...")
    try:
        conn2 = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database=dbname
        )
    except Exception as e:
        log(f"  Trying without password...")
        conn2 = await asyncpg.connect(
            host=host, port=port, user=user, database=dbname
        )
    
    sql = (ROOT / 'db' / 'migration_001_init.sql').read_text(encoding='utf-8')
    try:
        await conn2.execute(sql)
        log("  Migration done OK")
    except Exception as e:
        if 'already exists' in str(e):
            log(f"  Tables already exist (OK): {e}")
        else:
            log(f"  Migration warning: {e}")
    await conn2.close()

def main():
    log("=== ATWK Python Test Runner ===")
    env = read_env()
    log(f"DB: {env.get('ATWK_DB_HOST')}:{env.get('ATWK_DB_PORT')}/{env.get('ATWK_DB_NAME')}")

    # Step 1: DB setup
    log("\n[1/4] Database setup...")
    asyncio.run(setup_db(env))

    # Step 2: Start uvicorn
    log("\n[2/4] Starting uvicorn on port 8300...")
    server = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'api.main:app', '--reload', '--port', '8300'],
        cwd=str(ROOT),
        env={**os.environ, **{k: v for k, v in env.items()}}
    )
    log("  Waiting 10s for server to start...")
    time.sleep(10)

    # Step 3: Check server health
    log("\n[3/4] Checking server health...")
    import urllib.request
    for attempt in range(5):
        try:
            with urllib.request.urlopen('http://localhost:8300/api/v1/health', timeout=5) as r:
                log(f"  Health OK: {r.read().decode()[:100]}")
                break
        except Exception as e:
            log(f"  Attempt {attempt+1}: {e}")
            time.sleep(3)
    
    # Step 4: Run e2e tests
    log("\n[4/4] Running e2e tests...")
    log("=" * 50)
    result = subprocess.run(
        [sys.executable, str(ROOT / 'tests' / 'e2e_test.py')],
        cwd=str(ROOT),
        env={**os.environ, **{k: v for k, v in env.items()}}
    )
    log("=" * 50)
    if result.returncode == 0:
        log("RESULT: ALL TESTS PASSED!")
    else:
        log(f"RESULT: Some tests failed (exit code {result.returncode})")

    server.terminate()
    log("\nDone.")

if __name__ == '__main__':
    main()
