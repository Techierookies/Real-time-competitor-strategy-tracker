import sqlite3
import sys

DB_NAME = "competitor_tracker.db"

def search_in_raw_html(keywords, limit=6):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, model, site, raw_html FROM raw_scrapes ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(" No rows found in raw_scrapes.")
        return
    # Normalize keywords to lowercase for matching
    keywords_lc = [k.lower() for k in keywords]
    # For each row, check each keyword and print results
    for row in rows:
        row_id, model, site, raw_html = row
        raw_lc = (raw_html or "").lower()
        print(f"\n--- Row {row_id}: {model} ({site}) ---")
        found_any = False
        for kw, kw_lc in zip(keywords, keywords_lc):
            idx = raw_lc.find(kw_lc)
            if idx != -1:
                # show context around match
                start = max(0, idx - 120)
                end = min(len(raw_html), idx + 120)
                snippet = raw_html[start:end].replace("\n", " ").replace("\r", " ")
                print(f"\n Found keyword '{kw}' (case-insensitive):")
                print("... " + snippet + " ...")
                found_any = True
            else:
                print(f"\n Keyword '{kw}' not found in this row.")
        if not found_any:
            print("\n(→ No keywords from the list were found in this row.)")
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # usage: python search_raw_html.py ₹ review star
        keywords = sys.argv[1:]
    else:
        # default keywords to check (you can change these)
        keywords = ["₹", "review", "star"]
    # default limit of latest rows to search
    LIMIT = 6
    search_in_raw_html(keywords, limit=LIMIT)
