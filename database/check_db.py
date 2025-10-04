import sqlite3
conn = sqlite3.connect("competitor_tracker.db")
cursor = conn.cursor()
cursor.execute("SELECT id, model, site, scraped_at FROM raw_scrapes ORDER BY id")
rows = cursor.fetchall()
conn.close()

print("Raw data entries:")
for row in rows:
    print(row)
