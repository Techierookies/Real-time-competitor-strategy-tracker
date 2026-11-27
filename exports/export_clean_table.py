import sqlite3
import os
import html

DB_NAME = "competitor_tracker.db"
TABLE_NAME = "raw_scrapes"

def export_clean_table(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, model, site, price, rating, reviews FROM {TABLE_NAME} ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No rows found")
        return

    os.makedirs("exports", exist_ok=True)
    filename = "exports/clean_iphone_table.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html>\n<head>\n")
        f.write("<meta charset='UTF-8'>\n<title>iPhone Table</title>\n")
        f.write("<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>\n")
        f.write("</head>\n<body class='p-4'>\n")
        f.write("<h2 class='mb-4 text-center'>iPhone Price, Rating & Reviews</h2>\n")
        f.write("<div class='table-responsive'>\n")
        f.write("<table class='table table-bordered table-striped table-hover'>\n")
        f.write("<thead class='table-dark'><tr>\n")
        f.write("<th>ID</th><th>Model</th><th>Source</th><th>Price</th><th>Rating</th><th>Reviews</th>\n")
        f.write("</tr></thead>\n<tbody>\n")

        for row in rows:
            row_id, model, site, price, rating, reviews = row
            f.write(f"<tr><td>{row_id}</td><td>{html.escape(model)}</td><td>{html.escape(site)}</td>"
                    f"<td>{price}</td><td>{rating}</td><td>{reviews}</td></tr>\n")

        f.write("</tbody>\n</table>\n</div>\n</body>\n</html>")

    print(f"Exported {len(rows)} rows → {filename}")

if __name__ == "__main__":
    export_clean_table(limit=50)
