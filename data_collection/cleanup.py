import sqlite3

conn = sqlite3.connect("competitor_tracker.db")
cur = conn.cursor()

# Delete everything except Amazon and Flipkart URLs
cur.execute("DELETE FROM raw_scrapes WHERE site NOT IN ('amazon.in', 'flipkart.com')")
conn.commit()

# Optional: verify what remains
for row in cur.execute("SELECT DISTINCT site FROM raw_scrapes"):
    print(row)

conn.close()
