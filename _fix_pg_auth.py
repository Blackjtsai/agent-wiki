"""Fix PostgreSQL auth: add trust rule for 127.0.0.1 so asyncpg can connect."""
import subprocess
import sys
from pathlib import Path

# Find psql
psql = None
for v in [17, 16, 15, 14, 13]:
    p = Path(f"C:/Program Files/PostgreSQL/{v}/bin/psql.exe")
    if p.exists():
        psql = str(p)
        print(f"Found psql: {psql}")
        break

if not psql:
    print("ERROR: psql not found in standard locations")
    sys.exit(1)

# Step 1: Set postgres password to '123' via SSPI (no password needed for this call)
print("\n[1/3] Setting postgres password to '123'...")
r = subprocess.run(
    [psql, "-h", "127.0.0.1", "-U", "postgres", "-c",
     "ALTER USER postgres PASSWORD '123';", "postgres"],
    capture_output=True, text=True
)
print(f"  stdout: {r.stdout.strip()}")
print(f"  stderr: {r.stderr.strip()}")
print(f"  returncode: {r.returncode}")

# Step 2: Get pg_hba.conf path
print("\n[2/3] Getting pg_hba.conf path...")
r2 = subprocess.run(
    [psql, "-h", "127.0.0.1", "-U", "postgres", "-t", "-c",
     "SHOW hba_file;", "postgres"],
    capture_output=True, text=True
)
hba_path = r2.stdout.strip()
print(f"  pg_hba.conf: '{hba_path}'")
print(f"  stderr: {r2.stderr.strip()}")

if not hba_path:
    print("ERROR: Could not get pg_hba.conf path")
    sys.exit(1)

hba_file = Path(hba_path)
if not hba_file.exists():
    print(f"ERROR: pg_hba.conf not found at {hba_path}")
    sys.exit(1)

# Step 3: Read and modify pg_hba.conf
print("\n[3/3] Modifying pg_hba.conf...")
content = hba_file.read_text(encoding='utf-8', errors='replace')
print("--- Current content (first 800 chars) ---")
print(content[:800])
print("---")

trust_rule = "host    all             all             127.0.0.1/32            trust\n"

if "127.0.0.1/32            trust" in content:
    print("Trust rule already present, skipping")
else:
    # Prepend the trust rule so it matches before other rules
    new_content = trust_rule + content
    try:
        hba_file.write_text(new_content, encoding='utf-8')
        print(f"SUCCESS: Added trust rule to {hba_path}")
    except PermissionError as e:
        print(f"PERMISSION ERROR writing pg_hba.conf: {e}")
        print("Trying to show pg_hba.conf location for manual edit...")
        print(f"  File: {hba_path}")
        print(f"  Add this line at the TOP of that file:")
        print(f"  {trust_rule}")
        sys.exit(1)

# Reload PostgreSQL config
print("\nReloading PostgreSQL config...")
r3 = subprocess.run(
    [psql, "-h", "127.0.0.1", "-U", "postgres", "-c",
     "SELECT pg_reload_conf();", "postgres"],
    capture_output=True, text=True
)
print(f"  stdout: {r3.stdout.strip()}")
print(f"  stderr: {r3.stderr.strip()}")

print("\nDone! Now try connecting with asyncpg (no password needed).")
print("Update .env: ATWK_DB_PASSWORD=")
