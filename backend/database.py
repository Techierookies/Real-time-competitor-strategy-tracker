import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect("iphone_store.db", check_same_thread=False)
cursor = conn.cursor()

# Users table (user + admin)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'   -- 'user' ya 'admin'
)
""")

conn.commit()
