import asyncio
import datetime
import sqlite3
from crawl4ai import AsyncWebCrawler
DB_NAME = "competitor_tracker.db"
def save_raw_scrape(model, site, url, raw_html):
    """Save raw HTML into SQLite DB"""
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

async def fetch_with_crawlai(url):
    """Fetch raw HTML using Crawl4AI"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return getattr(result, "html", None) or getattr(result, "text", None) or getattr(result, "markdown", "")
async def main():
    # List of models with their URLs on Amazon + Flipkart
    targets = [
        ("iPhone 15", "Amazon", "https://www.amazon.in/s?k=iPhone+15"),
        ("iPhone 16", "Amazon", "https://www.amazon.in/s?k=iPhone+16"),
        ("iPhone 17", "Amazon", "https://www.amazon.in/s?k=iPhone+17"),
        ("iPhone 15", "Flipkart", "https://www.flipkart.com/search?q=iPhone+15"),
        ("iPhone 16", "Flipkart", "https://www.flipkart.com/search?q=iPhone+16"),
        ("iPhone 17", "Flipkart", "https://www.flipkart.com/search?q=iPhone+17"),
    ]
    for model, site, url in targets:
        print(f" Fetching {model} from {site} ({url}) ...")
        raw_html = await fetch_with_crawlai(url)
        save_raw_scrape(model, site, url, raw_html)
if __name__ == "__main__":
    print("=== CrawlAI Scraper Run Started ===")
    asyncio.run(main())
    print("=== CrawlAI Scraper Run Completed ===")
