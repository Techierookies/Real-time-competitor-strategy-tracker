import sqlite3
import sys
import textwrap
DB_NAME = "competitor_tracker.db"
def show_latest_raw(limit=21):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.model, r.site, r.url, r.raw_html, r.scraped_at,
               d.price, d.rating, d.review_count
        FROM raw_scrapes r
        LEFT JOIN dynamic_info d
        ON r.model = d.model AND r.site = d.site AND r.url = d.url
        ORDER BY r.id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print(" No rows found in raw_scrapes.")
        return
    for row in rows:
        row_id, model, site, url, raw_html, scraped_at, price, rating, reviews = row
        print("="*100)
        print(f"Row {row_id} | {model} | {site}")
        print(f"URL: {url}")
        print(f" Scraped: {scraped_at}")
        print(f"Price: {price or 'N/A'} | Rating: {rating or 'N/A'} |  Reviews: {reviews or 'N/A'}")
        print("-"*100)
        snippet = (raw_html or "")[:2000]
        print(textwrap.fill(snippet, width=120))
        if len(raw_html or "") > 2000:
            print("\n... (truncated) ...")
    print("="*100)
    print(f"Displayed latest {len(rows)} rows.")
if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 21
    show_latest_raw(limit=limit)