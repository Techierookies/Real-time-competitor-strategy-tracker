import sqlite3
import os
import sys
import html
DB_NAME = "competitor_tracker.db"
def export_latest_raw_html(limit=21):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.model, r.site, r.url, r.raw_html, d.price, d.rating, d.review_count, r.scraped_at
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
    os.makedirs("exports", exist_ok=True)
    output_file = "exports/export_with_dynamic.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<!doctype html><html><head><meta charset='utf-8'>")
        f.write("<title>Exported Competitor Pages</title>")
        f.write("<style>")
        f.write("""
        body{font-family:Arial, sans-serif; margin:20px;}
        .entry{border:2px solid #ccc; margin:20px 0; padding:12px; border-radius:8px;}
        .meta{color:#555; font-size:0.95em; margin-bottom:8px;}
        iframe{width:100%; height:500px; border:1px solid #888;}
        table{border-collapse:collapse; margin-top:10px;}
        td,th{border:1px solid #aaa; padding:6px 10px;}
        th{background:#f4f4f4;}
        """)
        f.write("</style></head><body>")
        f.write("<h1>Exported Raw HTML + Dynamic Data</h1>")
        for row in rows:
            row_id, model, site, url, raw_html, price, rating, reviews, scraped_at = row
            f.write("<div class='entry'>")
            f.write(f"<h2>{model} ({site})</h2>")
            f.write(f"<div class='meta'>Row {row_id} | Scraped: {scraped_at}</div>")
            f.write(f"<div><b>URL:</b> <a href='{url}' target='_blank'>{url}</a></div>")
            f.write("<table><tr><th>Price</th><th>Rating</th><th>Reviews</th></tr>")
            f.write(f"<tr><td>{price or 'N/A'}</td><td>{rating or 'N/A'}</td><td>{reviews or 'N/A'}</td></tr></table>")
            f.write("<hr>")
            safe_html = html.escape(raw_html or "")
            f.write(f"<iframe srcdoc=\"{safe_html}\"></iframe>")
            f.write("</div>\n")
        f.write("</body></html>")
    print(f" Exported {len(rows)} rows → {output_file}")
if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 21
    export_latest_raw_html(limit=limit)