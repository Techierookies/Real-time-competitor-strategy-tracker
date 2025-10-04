import sqlite3
DB_NAME = "competitor_tracker.db"
def show_all_raw_html(limit=3):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, model, site, url, raw_html FROM raw_scrapes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("❌ No rows found")
        return
    for row in rows:
        id, model, site, url, raw_html = row
        print(f"\n--- Row ID: {id} ---")
        print(f"Model: {model}")
        print(f"Site: {site}")
        print(f"URL: {url}")
        print("--- Raw HTML (first 500 chars) ---")
        print(raw_html[:500])  # print only part to avoid huge dump
        print("\n---------------------------")
if __name__ == "__main__":
    # show the 6 most recent entries (3 Amazon + 3 Flipkart)
    show_all_raw_html(limit=6)
