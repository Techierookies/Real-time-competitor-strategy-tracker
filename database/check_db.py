import sqlite3

DB_NAME = "competitor_tracker.db"
TABLE_NAME = "raw_scrapes"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Get existing columns
cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
columns_info = cursor.fetchall()
columns = [col[1] for col in columns_info]

# Build SELECT query dynamically based on available columns
select_columns = ", ".join(columns)
cursor.execute(f"SELECT {select_columns} FROM {TABLE_NAME} ORDER BY id")
rows = cursor.fetchall()
conn.close()

# Print header
header = " | ".join(f"{col:^15}" for col in columns)
separator = "-" * len(header)
print(separator)
print(header)
print(separator)

# Print rows
for row in rows:
    row_str = " | ".join(f"{str(val)[:15]:^15}" for val in row)  # truncate long text to 15 chars
    print(row_str)

print(separator)
print(f"Total rows: {len(rows)}")
