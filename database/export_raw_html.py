import sqlite3
import os
import html
DB_NAME = "competitor_tracker.db"
def export_latest_raw_html(limit=6):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, model, site, raw_html FROM raw_scrapes ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print(" No rows found")
        return
    os.makedirs("exports", exist_ok=True)
    combined_filename = "exports/combined_raw_export.html"
    # Build HTML file
    with open(combined_filename, "w", encoding="utf-8") as f:
        f.write("<!doctype html>\n<html>\n<head>\n")
        f.write("<meta charset='utf-8'>\n")
        f.write("<title>Combined Raw Export</title>\n")
        f.write("<style>\n")
        f.write("body{font-family:Arial, sans-serif; margin:20px}\n")
        f.write(".toc{background:#f7f7f7; padding:15px; border-radius:6px}\n")
        f.write(".entry{border:2px solid #ccc; margin:20px 0; padding:12px}\n")
        f.write(".entry h2{margin:0 0 10px 0}\n")
        f.write(".meta{color:#555; font-size:0.95em; margin-bottom:8px}\n")
        f.write("</style>\n")
        f.write("</head>\n<body>\n")
        f.write("<h1>Exported Raw HTML Pages</h1>\n")
        f.write("<div class='toc'>\n")
        f.write("<h3>Table of contents</h3>\n")
        f.write("<ul>\n")
        for row in rows:
            row_id, model, site, raw_html = row
            anchor = f"row-{row_id}"
            f.write(f"<li><a href='#{anchor}'>Row {row_id}: {html.escape(model)} ({html.escape(site)})</a></li>\n")
        f.write("</ul>\n")
        f.write("</div>\n\n")
        # Insert each raw HTML under its anchor, with a back-to-top link
        for row in rows:
            row_id, model, site, raw_html = row
            anchor = f"row-{row_id}"
            f.write(f"<section id='{anchor}' class='entry'>\n")
            f.write(f"<h2>Row {row_id}: {html.escape(model)} ({html.escape(site)})</h2>\n")
            f.write(f"<div class='meta'>Row ID: {row_id} &nbsp; | &nbsp; Model: {html.escape(model)} &nbsp; | &nbsp; Site: {html.escape(site)}</div>\n")
            try:
                safe_content = raw_html if raw_html else ""
                max_srcdoc = 1000000  # 1 MB
                srcdoc_content = safe_content[:max_srcdoc]
                srcdoc_content = srcdoc_content.replace("</script>", "<\\/script>")
                f.write("<div style='margin-bottom:8px;'>\n")
                f.write(f"<iframe style='width:100%; height:600px; border:1px solid #999' srcdoc=\"{html.escape(srcdoc_content)}\"></iframe>\n")
                f.write("</div>\n")
            except Exception:
                f.write("<div style='max-height:600px; overflow:auto; background:#fff; padding:10px; border:1px dashed #ddd;'>\n")
                f.write("<pre style='white-space:pre-wrap; font-size:12px;'>\n")
                f.write(html.escape(raw_html[:50000]))  # show up to 50k chars
                f.write("\n</pre>\n</div>\n")
            f.write("<p><a href='#top'>Back to top</a></p>\n")
            f.write("</section>\n\n")
        f.write("</body>\n</html>")
    print(f"Exported {len(rows)} rows into one file → {combined_filename}")
if __name__ == "__main__":
    # default limit is 6 (you can change it if needed)
    export_latest_raw_html(limit=6)