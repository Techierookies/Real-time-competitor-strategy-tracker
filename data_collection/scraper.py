import datetime
import sqlite3

DB_NAME = "competitor_tracker.db"

def save_raw_scrape(model, site, url, raw_html):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    scraped_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO raw_scrapes (model, site, url, raw_html, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (model, site, url, raw_html, scraped_at))

    conn.commit()
    conn.close()
    print(f"Raw data saved for {model} from {site}")

if __name__ == "__main__":
    # Day 3: 3 models
    models = ["iPhone 15", "iPhone 16", "iPhone 17"]
    site = "Amazon"

    for model in models:
        url = f"https://www.amazon.in/s?k={model.replace(' ', '+')}"  # dummy URL
        raw_html = (
            f"<html><body>"
            f"<h1>{model} - Dummy Price</h1>"
            f"<p>Rating: Dummy</p>"
            f"<p>Review: Dummy Review for {model}</p>"
            f"</body></html>"
        )
        save_raw_scrape(model, site, url, raw_html)


