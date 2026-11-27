import sqlite3
DB="competitor_tracker.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
SELECT id, model, site, price, rating, review_count, extracted_at
FROM dynamic_info
WHERE model IS NOT NULL AND site IS NOT NULL
ORDER BY model, site, datetime(extracted_at) DESC, id DESC
""")
rows = cur.fetchall()
from collections import defaultdict
g=defaultdict(list)
for r in rows:
    idd, model, site, price, rating, rc, ext = r
    key=(model,site)
    if len(g[key])<2:
        g[key].append((idd, price, rating, rc, ext))
for key in sorted(g.keys()):
    print("==", key, "==")
    for item in g[key]:
        print(item)
print("done")
conn.close()
