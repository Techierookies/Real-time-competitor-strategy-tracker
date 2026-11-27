import sqlite3
import shutil
from pathlib import Path

# Paths
base_dir = Path(__file__).resolve().parent
backend_db = base_dir / "competitor_tracker.db"
teammate_db = base_dir.parent / "competitor_tracker.db"

# Backup first
shutil.copy(backend_db, backend_db.with_name("competitor_tracker_backup.db"))

# Connect to both DBs
conn_backend = sqlite3.connect(backend_db)
conn_team = sqlite3.connect(teammate_db)
cb = conn_backend.cursor()
ct = conn_team.cursor()

# Get all tables from teammate DB
ct.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in ct.fetchall()]

for table in tables:
    print(f"Merging table: {table}")
    # Check if table exists in backend DB
    cb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    exists = cb.fetchone()

    # Create table if missing
    if not exists:
        ct.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        create_sql = ct.fetchone()[0]
        cb.execute(create_sql)

    # Copy all rows
    ct.execute(f"SELECT * FROM {table}")
    rows = ct.fetchall()

    if rows:
        placeholders = ",".join(["?"] * len(rows[0]))
        try:
            cb.executemany(f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})", rows)
        except Exception as e:
            print(f"⚠️ Skipped {table}: {e}")

conn_backend.commit()
conn_backend.close()
conn_team.close()

print("✅ Merge complete! All data combined into backend DB.")
