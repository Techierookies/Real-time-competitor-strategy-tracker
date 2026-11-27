import sqlite3
import pandas as pd

DB_NAME = "competitor_tracker.db"
TABLE_NAME = "raw_scrapes"

# Connect to DB
conn = sqlite3.connect(DB_NAME)

# Read table into DataFrame
df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)

# Export to CSV
df.to_csv("raw_scrapes_export.csv", index=False)

# Export to JSON (optional)
df.to_json("raw_scrapes_export.json", orient="records", indent=4)

conn.close()
print("✅ Exported to raw_scrapes_export.csv and raw_scrapes_export.json")
