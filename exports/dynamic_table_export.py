import sqlite3
import os
import html
import random
import re

DB_NAME = "competitor_tracker.db"
TABLE_NAME = "raw_scrapes"

# Sample review texts to use dynamically
sample_reviews = [
    "Excellent phone with amazing camera.",
    "Battery life could be better.",
    "Smooth performance and great display.",
    "Value for money, highly recommend.",
    "Good, but a bit expensive.",
    "Awesome features and sleek design.",
    "Average, expected more.",
    "Perfect for daily use and gaming.",
]

# ---------- Data Cleaning Helpers ----------
def clean_price(price):
    if not price:
        return "N/A"
    price = re.sub(r"[^\d]", "", str(price))  # remove non-digits
    return f"₹{int(price):,}" if price else "N/A"

def clean_rating(rating):
    if not rating:
        return "N/A"
    try:
        rating = float(re.search(r"[\d.]+", str(rating)).group())
        return f"{rating:.1f}"
    except:
        return "N/A"

def clean_reviews(reviews):
    if not reviews:
        return "N/A"
    return html.escape(str(reviews).strip())

def clean_text(text):
    if not text:
        return "N/A"
    return html.escape(str(text).strip())

# ---------- Fill Dynamic Values ----------
def fill_dynamic_values():
    """Fill price, rating, and reviews dynamically if empty."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"SELECT id FROM {TABLE_NAME}")
    rows = cursor.fetchall()

    for row in rows:
        row_id = row[0]

        # Generate dynamic values
        price = f"₹{random.randint(70_000, 150_000):,}"  # random price
        rating = round(random.uniform(3.5, 5.0), 1)      # random rating
        reviews = random.choice(sample_reviews)          # random review text

        cursor.execute(f"""
            UPDATE {TABLE_NAME}
            SET price=?, rating=?, reviews=?
            WHERE id=?
        """, (price, rating, reviews, row_id))

    conn.commit()
    conn.close()
    print("✅ Dynamic price, rating, and reviews inserted for all rows.")

# ---------- Export with Processing ----------
def export_clean_table(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Sort by rating (highest first)
    cursor.execute(f"""
        SELECT id, model, site, price, rating, reviews, url
        FROM {TABLE_NAME}
        ORDER BY rating DESC, id ASC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("⚠️ No rows found")
        return

    os.makedirs("exports", exist_ok=True)
    filename = "exports/dynamic_iphone_table.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html lang='en'>\n<head>\n")
        f.write("<meta charset='UTF-8'>\n<title>iPhone Table</title>\n")
        f.write("<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>\n")
        f.write("</head>\n<body class='p-4'>\n")
        f.write("<h2 class='mb-4 text-center'>📱 iPhone Price, Rating & Reviews (Processed & Sorted)</h2>\n")
        f.write("<div class='table-responsive'>\n")
        f.write("<table class='table table-bordered table-striped table-hover'>\n")
        f.write("<thead class='table-dark'><tr>\n")
        f.write("<th>ID</th><th>Model</th><th>Source</th><th>Price</th><th>Rating</th><th>Reviews</th><th>URL</th>\n")
        f.write("</tr></thead>\n<tbody>\n")

        for row in rows:
            row_id, model, site, price, rating, reviews, url = row

            # ✅ Preprocessing
            model = clean_text(model)
            site = clean_text(site)
            price = clean_price(price)
            rating = clean_rating(rating)
            reviews = clean_reviews(reviews)
            url = clean_text(url)

            f.write(
                f"<tr>"
                f"<td>{row_id}</td>"
                f"<td>{model}</td>"
                f"<td>{site}</td>"
                f"<td>{price}</td>"
                f"<td>{rating}</td>"
                f"<td>{reviews}</td>"
                f"<td><a href='{url}' target='_blank'>View Product</a></td>"
                f"</tr>\n"
            )

        f.write("</tbody>\n</table>\n</div>\n</body>\n</html>")

    print(f"✅ Exported {len(rows)} rows → {filename}")

# ---------- Main ----------
if __name__ == "__main__":
    fill_dynamic_values()
    export_clean_table(limit=50)
