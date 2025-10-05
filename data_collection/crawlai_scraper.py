import asyncio
import sqlite3
import datetime
import re
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
DB = "competitor_tracker.db"
CRAWL_TIMEOUT = 60
PLAYWRIGHT_TIMEOUT_MS = 12000
MODELS = ["iPhone 15", "iPhone 16", "iPhone 17"]
SITES = [
    "amazon.in",
    "flipkart.com",
    "croma.com",
    "reliancedigital.in",
    "vijaysales.com",
    "tatacliq.com",
    "paytmmall.com"
]
STATIC_URL_PATTERNS = {
    "amazon.in": "https://www.amazon.in/s?k={q}",
    "flipkart.com": "https://www.flipkart.com/search?q={q}",
    "croma.com": "https://www.croma.com/search/?text={q}",
    "reliancedigital.in": "https://www.reliancedigital.in/search?q={q}",
    "vijaysales.com": "https://www.vijaysales.com/search/{q}",
    "tatacliq.com": "https://www.tatacliq.com/search/?search={q}",
    "paytmmall.com": "https://www.paytmmall.com/shop/search?q={q}"
}
def ensure_tables():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_scrapes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            site TEXT,
            url TEXT,
            raw_html TEXT,
            scraped_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            site TEXT,
            url TEXT,
            price REAL,
            rating REAL,
            review_count INTEGER,
            extracted_at TEXT
        )
    """)
    conn.commit()
    conn.close()
def save_raw_scrape(model, site, url, raw_html):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    scraped_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO raw_scrapes (model, site, url, raw_html, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (model, site, url, raw_html, scraped_at))
    conn.commit()
    conn.close()
    print(f" Saved HTML for {model} ({site})")
def save_dynamic_info(model, site, url, price, rating, reviews):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    extracted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO dynamic_info (model, site, url, price, rating, review_count, extracted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (model, site, url, price, rating, reviews, extracted_at))
    conn.commit()
    conn.close()
    print(f" Stored dynamic info → Price: {price}, Rating: {rating}, Reviews: {reviews}")
def extract_dynamic_info(html):
    """Extract price, rating, and reviews dynamically from HTML."""
    if not html:
        return None, None, None
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    price = rating = reviews = None
    m = re.search(r"₹\s?([\d,]+)", text) or re.search(r"Rs\.?\s?([\d,]+)", text)
    if m:
        try:
            price = float(m.group(1).replace(",", ""))
        except:
            pass
    r = re.search(r"([0-5]\.?[0-9]?)\s*(?:out of 5|/5|stars|⭐)", text, re.I)
    if r:
        try:
            rating = float(r.group(1))
        except:
            pass
    rv = re.search(r"([\d,]+)\s+(?:reviews|ratings)", text, re.I)
    if rv:
        try:
            reviews = int(rv.group(1).replace(",", ""))
        except:
            pass
    return price, rating, reviews
async def crawlai_fetch(url):
    """Fetch HTML using CrawlAI."""
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, timeout=CRAWL_TIMEOUT)
            return getattr(result, "html", None) or getattr(result, "text", None) or ""
    except Exception as e:
        print(f" CrawlAI failed for {url}: {e}")
        return ""

def playwright_render(url):
    """Fallback using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS)
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f" Playwright failed for {url}: {e}")
        return ""
async def process_url(model, site, url):
    print(f"\n Scraping {model} ({site}) → {url}")
    html = await crawlai_fetch(url)
    if not html.strip():
        print(" Empty page — retrying with Playwright...")
        html = await asyncio.to_thread(playwright_render, url)
    if html.strip():
        save_raw_scrape(model, site, url, html)
        price, rating, reviews = extract_dynamic_info(html)
        save_dynamic_info(model, site, url, price, rating, reviews)
    else:
        print(f" Failed for {model} ({site})")
async def main():
    ensure_tables()
    print("=== Dynamic Data Collector Started ===")
    targets = []
    for model in MODELS:
        q = model.replace(" ", "+")
        for site in SITES:
            pattern = STATIC_URL_PATTERNS.get(site)
            if pattern:
                url = pattern.format(q=q)
                targets.append((model, site, url))
    print("\n All URLs to scrape:")
    for m, s, u in targets:
        print(f"  - {m} | {s} | {u}")
    success = 0
    for model, site, url in targets:
        try:
            await process_url(model, site, url)
            success += 1
        except Exception as e:
            print(f" Error for {model} ({site}): {e}")
    print(f"\n Crawl completed — {success}/{len(targets)} pages scraped successfully")
if __name__ == "__main__":
    asyncio.run(main())