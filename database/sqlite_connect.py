import sqlite3

DB_NAME = "competitor_tracker.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_scrapes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            site TEXT,
            url TEXT,
            raw_html TEXT,
            scraped_at TEXT
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Raw data table created successfully")

