import sqlite3
import os
import html
from bs4 import BeautifulSoup

DB_NAME = "competitor_tracker.db"

def extract_field_from_html(html_content, field_name):
    # Example parsing logic (adjust selectors to your raw HTML)
    soup = BeautifulSoup(html_content, "html.parser")
    if field_name == "price":
        tag = soup.select_one(".price")  # change selector to match your HTML
        return tag.text.strip() if tag else "N/A"
    elif field_name == "rating":
        tag = soup.select_one(".rating")
        return tag.text.strip() if tag else "N/A"
    elif field_name == "reviews":
        tag = soup.select_one(".reviews")
        return tag.text.strip() if tag else "N/A"
    return "N/A"

def export_structured_table(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, model, site, raw_html FROM raw_scrapes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No rows found")
        return

    os.makedirs("exports", exist_ok=True)
    filename = "exports/iphone_table.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html>\n<head>\n")
        f.write("<meta charset='utf-8'>\n")
        f.write("<title>iPhone Data Table</title>\n")
        f.write("<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>\n")
        f.write("</head>\n<body class='p-4'>\n")
        f.write("<h2 class='mb-4 text-center'>iPhone Price, Rating & Reviews</h2>\n")
        f.write("<div class='table-responsive'>\n")
        f.write("<table class='table table-bordered table-striped table-hover'>\n")
        f.write("<thead class='table-dark'><tr>\n")
        f.write("<th>ID</th><th>Model</th><th>Source</th><th>Price</th><th>Rating</th><th>Reviews</th>\n")
        f.write("</tr></thead>\n<tbody>\n")

        for row in rows:
            row_id, model, site, raw_html = row
            price = extract_field_from_html(raw_html, "price")
            rating = extract_field_from_html(raw_html, "rating")
            reviews = extract_field_from_html(raw_html, "reviews")
            f.write(f"<tr><td>{row_id}</td><td>{html.escape(model)}</td><td>{html.escape(site)}</td><td>{price}</td><td>{rating}</td><td>{reviews}</td></tr>\n")

        f.write("</tbody>\n</table>\n</div>\n</body>\n</html>")

    print(f"Exported {len(rows)} rows → {filename}")

if __name__ == "__main__":
    export_structured_table(limit=50)
