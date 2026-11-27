# Competitor Strategy Tracker — Data Collection (Days 1–7)
- Collects raw HTML of competitor product pages (iPhone 15/16/17) from Amazon and Flipkart using `crawl4ai`.
- Stores raw HTML in `competitor_tracker.db` inside the `raw_scrapes` table.
- Keeps metadata: `model`, `site`, `url`, and `scraped_at` (timestamp).
- Builds **history**: every new scrape creates a new row with a new timestamp.
##  Project Structure (your part)
database/
├── sqlite_connect.py # creates DB + tables
├── check_db.py # lists all rows in DB
├── show_raw_html.py # shows latest HTML snippets
├── export_raw_html.py # exports rows into combined HTML file
├── search_raw_html.py # search keywords (₹, review, star)
data_collection/
├── scraper.py # dummy data scraper (Day 2–3)
└── crawlai_scraper.py # real scraper with Crawl4AI (Day 4–7)