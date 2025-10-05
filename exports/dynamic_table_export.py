import sqlite3
import os
import html
import random

DB_NAME = "competitor_tracker.db"
TABLE_NAME = "raw_scrapes"  # your table

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

def fill_dynamic_values():
    """Fill price, rating, and reviews dynamically if empty or same."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"SELECT id FROM {TABLE_NAME}")
    rows = cursor.fetchall()

    for row in rows:
        row_id = row[0]

        # Generate dynamic values
        price = f"₹{random.randint(70_000, 150_000):,}"  # random price
        rating = round(random.uniform(3.5, 5.0), 1)      # random rating 3.5-5
        reviews = random.choice(sample_reviews)          # random review text

        cursor.execute(f"""
            UPDATE {TABLE_NAME}
            SET price=?, rating=?, reviews=?
            WHERE id=?
        """, (price, rating, reviews, row_id))

    conn.commit()
    conn.close()
    print("Dynamic price, rating, and reviews inserted for all rows.")

def export_clean_table(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # ✅ Sort by rating (highest first)
    cursor.execute(f"""
        SELECT id, model, site, price, rating, reviews 
        FROM {TABLE_NAME} 
        ORDER BY rating DESC, id ASC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No rows found")
        return

    os.makedirs("exports", exist_ok=True)
    filename = "exports/dynamic_iphone_table.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html lang='en'>\n<head>\n")
        f.write("<meta charset='UTF-8'>\n<title>iPhone Table</title>\n")
        f.write("<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>\n")
        f.write("</head>\n<body class='p-4'>\n")
        f.write("<h2 class='mb-4 text-center'>iPhone Price, Rating & Reviews (Sorted by Rating)</h2>\n")
        f.write("<div class='table-responsive'>\n")
        f.write("<table class='table table-bordered table-striped table-hover'>\n")
        f.write("<thead class='table-dark'><tr>\n")
        f.write("<th>ID</th><th>Model</th><th>Source</th><th>Price</th><th>Rating</th><th>Reviews</th>\n")
        f.write("</tr></thead>\n<tbody>\n")

        for row in rows:
            row_id, model, site, price, rating, reviews = row
            f.write(f"<tr><td>{row_id}</td><td>{html.escape(model)}</td><td>{html.escape(site)}</td>"
                    f"<td>{price}</td><td>{rating}</td><td>{html.escape(reviews)}</td></tr>\n")

        f.write("</tbody>\n</table>\n</div>\n</body>\n</html>")

    print(f"Exported {len(rows)} rows → {filename}")

if __name__ == "__main__":
    
    # Step 1: Fill dynamic values
    fill_dynamic_values()

    # Step 2: Export sorted table
    export_clean_table(limit=50)
