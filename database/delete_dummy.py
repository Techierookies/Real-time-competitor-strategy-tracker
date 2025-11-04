import sqlite3
conn = sqlite3.connect("competitor_tracker.db")
cur = conn.cursor()
# delete rows where raw_html has the word "Dummy"
cur.execute("DELETE FROM raw_scrapes WHERE raw_html LIKE '%Dummy%';")
conn.commit()
print("Deleted dummy rows.")
conn.close()
