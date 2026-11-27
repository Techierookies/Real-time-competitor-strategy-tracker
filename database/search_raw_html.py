import sqlite3
import sys
DB_NAME = "competitor_tracker.db"
def search_in_raw_html(keywords, limit=21):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.model, r.site, r.url, r.raw_html, d.price, d.rating, d.review_count
        FROM raw_scrapes r
        LEFT JOIN dynamic_info d
        ON r.model = d.model AND r.site = d.site AND r.url = d.url
        ORDER BY r.id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print(" No rows found.")
        return
    keywords_lower = [k.lower() for k in keywords]
    for row in rows:
        row_id, model, site, url, raw_html, price, rating, reviews = row
        raw_lower = (raw_html or "").lower()
        print("\n" + "="*80)
        print(f"Row {row_id} | {model} | {site}")
        print(f"URL: {url}")
        print(f" Price: {price or 'N/A'} |  Rating: {rating or 'N/A'} |  Reviews: {reviews or 'N/A'}")
        print("-"*80)
        found_any = False
        for kw, kw_lower in zip(keywords, keywords_lower):
            idx = raw_lower.find(kw_lower)
            if idx != -1:
                start = max(0, idx - 100)
                end = min(len(raw_html or ""), idx + 100)
                snippet = (raw_html or "")[start:end].replace("\n", " ").replace("\r", " ")
                print(f" Found '{kw}': ...{snippet}...")
                found_any = True
        if not found_any:
            print(" No keywords found in this row.")
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        *kw_args, last = sys.argv[1:]
        if last.isdigit():
            keywords = kw_args
            limit = int(last)
        else:
            keywords = sys.argv[1:]
            limit = 21
    else:
        keywords = ["₹", "rating", "review"]
        limit = 21
    search_in_raw_html(keywords, limit=limit)