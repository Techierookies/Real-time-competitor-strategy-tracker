import asyncio
import sqlite3
import datetime
import re
from pathlib import Path
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from playwright.async_api import async_playwright
DB = "competitor_tracker.db"
MODELS = ["iPhone 15", "iPhone 16", "iPhone 17"]
STATIC_URL_PATTERNS = {
    "amazon.in": "https://www.amazon.in/s?k={q}",
    "flipkart.com": "https://www.flipkart.com/search?q={q}"
}
MIN_PRICE = 50000.0
MAX_PRICE = 300000.0
CRAWLAI_TIMEOUT = 60
PLAYWRIGHT_TIMEOUT_MS = 20000
PLAYWRIGHT_HEADLESS = True# set False for debugging to see the browser
# --------------------------------------

# ---------- DB / helpers ----------
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
    scraped_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO raw_scrapes (model, site, url, raw_html, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (model, site, url, raw_html, scraped_at))
    conn.commit()
    conn.close()
    print(f"  [DB] raw_scrapes saved: {model} @ {site}")

def save_dynamic_info(model, site, url, price, rating, review_count):
    conn = sqlite3.connect(DB)   
    cur = conn.cursor()
    extracted_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO dynamic_info (model, site, url, price, rating, review_count, extracted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (model, site, url, price, rating, review_count, extracted_at))
    conn.commit()
    conn.close()
    print(f"  [DB] dynamic_info saved: {model} @ {site} → price={price} rating={rating} reviews={review_count}")

# ---------- Crawl4AI primary fetcher ----------
async def crawlai_fetch(url, timeout=CRAWLAI_TIMEOUT):
    try:
        async with AsyncWebCrawler() as crawler:
            # arun returns an object with .html or .text depending on response
            result = await crawler.arun(url=url, timeout=timeout)
            html = getattr(result, "html", None) or getattr(result, "text", None) or ""
            return html or ""
    except Exception as e:
        print(f"  [CrawlAI] fetch error for {url}: {e}")
        return ""

# ---------- Playwright fallback fetcher ----------
async def playwright_fetch(url, headless=PLAYWRIGHT_HEADLESS, timeout_ms=PLAYWRIGHT_TIMEOUT_MS):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_ms)
            await asyncio.sleep(2.5)   # allow JS to render (tunable)
            html = await page.content()
            await browser.close()
            return html or ""
    except Exception as e:
        print(f"  [Playwright] fetch error for {url}: {e}")
        return ""

# ---------- Extraction (site-aware, robust) ----------
def _parse_int_safe(s):
    if not s:
        return None
    s2 = re.sub(r"[^\d]", "", str(s))
    return int(s2) if s2.isdigit() else None

def extract_info(html, url_hint=None, model_hint=None):
    """
    Extract price, rating, review_count from HTML.
    url_hint helps pick site-specific selectors.
    """
    if not html:
        return None, None, None

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    url = (url_hint or "").lower()

    price = rating = review_count = None

    # ---------- AMAZON ----------
    if "amazon" in url:
        # price: prefer a-offscreen, then a-price-whole
        p_el = soup.select_one("span.a-price > span.a-offscreen") or soup.select_one("span.a-price-whole") or soup.select_one("span.a-color-price")
        if p_el:
            m = re.search(r"([\d,]+)", p_el.get_text(" ", strip=True))
            if m:
                try:
                    val = float(m.group(1).replace(",", ""))
                    if MIN_PRICE <= val <= MAX_PRICE:
                        price = val
                except:
                    pass
        # rating
        r_el = soup.select_one("span.a-icon-alt")
        if r_el:
            m = re.search(r"([0-5]\.?[0-9]?)", r_el.get_text())
            if m:
                try:
                    rating = float(m.group(1))
                except:
                    pass
        # review count
        rc_el = soup.select_one("span#acrCustomerReviewText")
        if rc_el:
            rc = _parse_int_safe(rc_el.get_text())
            if rc:
                review_count = rc

    # ---------- FLIPKART ----------
    if "flipkart" in url:
        # try product-page price selectors
        price_selectors = [
            "div._30jeq3._16Jk6d",
            "div._30jeq3",
            "div._25b18c span",
            "div._1vC4OE"
        ]
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                m = re.search(r"([\d,]+)", el.get_text(" ", strip=True))
                if m:
                    try:
                        v = float(m.group(1).replace(",", ""))
                        if MIN_PRICE <= v <= MAX_PRICE:
                            price = v
                            break
                    except:
                        pass

        # rating
        r_el = soup.select_one("div._3LWZlK")
        if r_el:
            try:
                rating = float(re.search(r"([0-5]\.?[0-9]?)", r_el.get_text()).group(1))
            except:
                pass

        # review count
        rc_el = soup.select_one("span._2_R_DZ") or soup.select_one("span._2c7YLP") or soup.select_one("span._1lRcqv")
        if rc_el:
            m = re.search(r"([\d,]+)", rc_el.get_text(" ", strip=True))
            if m:
                try:
                    review_count = int(m.group(1).replace(",", ""))
                except:
                    pass

    # ---------- FALLBACKS (generic) ----------
    if price is None:
        m = re.search(r"₹\s?([\d,]+)", text)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
                if MIN_PRICE <= v <= MAX_PRICE:
                    price = v
            except:
                pass

    if rating is None:
        m = re.search(r"([0-5]\.?[0-9]?)\s*(?:out of 5|/5|stars|⭐)", text, re.I)
        if m:
            try:
                rating = float(m.group(1))
            except:
                pass

    if review_count is None:
        m = re.search(r"([\d,]+)\s+(?:ratings|reviews)", text, re.I)
        if m:
            try:
                review_count = int(m.group(1).replace(",", ""))
            except:
                pass

    # final sanity
    if price is not None and (price < MIN_PRICE or price > MAX_PRICE):
        price = None

    return price, rating, review_count
# --- helper: visit product pages from a Flipkart listing to find price/rating/reviews ---
async def try_product_pages_for_price(model, site, listing_html, listing_url, max_pages=2):
    """
    Parse listing_html, extract candidate product links (Flipkart), visit up to max_pages product pages
    via Playwright and return first (price, rating, review_count) found (or (None,None,None)).
    """
    # parse listing HTML
    soup = BeautifulSoup(listing_html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        # Flipkart product URL heuristics
        if any(token in href for token in ["/p/", "/product/", "/itm/", "/apple-iphone"]):
            # normalize
            if href.startswith("http"):
                link = href.split("?")[0]
            else:
                link = "https://www.flipkart.com" + href.split("?")[0]
            if link not in links:
                links.append(link)
        if len(links) >= 10:  # gather a few candidates
            break

    # limit to first useful ones
    links = links[:max_pages]

    for pl in links:
        print(f"   Visiting product page (fallback): {pl}")
        # fetch rendered page
        ph = await playwright_fetch(pl, headless=PLAYWRIGHT_HEADLESS, timeout_ms=PLAYWRIGHT_TIMEOUT_MS)
        if not ph or not ph.strip():
            print("    Playwright failed for product page, skipping.")
            continue
        # save raw product page for debugging
        save_raw_scrape(model, site, pl, ph)
        # extract info from product page (pass product URL)
        p_price, p_rating, p_reviews = extract_info(ph, url_hint=pl, model_hint=model)
        print(f"    Product page extraction → price={p_price}, rating={p_rating}, reviews={p_reviews}")
        if p_price:  # first valid price wins
            return p_price, p_rating, p_reviews

    return None, None, None


# --- new process_target (replace existing one) ---
async def process_target(model, site, url):
    print(f"\n[SCRAPE] {model} @ {site} -> {url}")

    # 1) try CrawlAI
    html = await crawlai_fetch(url)
    used = "CrawlAI"
    if not html or not html.strip() or len(html) < 800:
        print("  CrawlAI returned insufficient HTML; using Playwright fallback...")
        html = await playwright_fetch(url, headless=PLAYWRIGHT_HEADLESS, timeout_ms=PLAYWRIGHT_TIMEOUT_MS)
        used = "Playwright"

    if not html or not html.strip():
        print("  FAILED: no HTML available for", url)
        return

    # save listing raw HTML
    save_raw_scrape(model, site, url, html)

    # extract structured info (pass url and model hint)
    price, rating, review_count = extract_info(html, url_hint=url, model_hint=model)

    # If Flipkart listing gave no price, try product pages (fallback)
    if "flipkart" in (url or "").lower() and (price is None):
        print("  Flipkart listing returned no price — trying product page fallback...")
        p_price, p_rating, p_reviews = await try_product_pages_for_price(model, site, html, url, max_pages=3)
        # if found, use them
        if p_price:
            price, rating, review_count = p_price, p_rating, p_reviews
            used = "Playwright(product-pages)"  

    print(f"  [{used}] Extracted → price={price}, rating={rating}, reviews={review_count}")


    save_dynamic_info(model, site, url, price, rating, review_count)
async def main():
    ensure_tables()
    print("=== CrawlAI-primary + Playwright-fallback scraper (Amazon & Flipkart) ===")
    targets = []
    for model in MODELS:
        q = model.replace(" ", "+")
        for site, pattern in STATIC_URL_PATTERNS.items():
            url = pattern.format(q=q)
            targets.append((model, site, url))
    for model, site, url in targets:
        await process_target(model, site, url)
    print("=== Scraping complete ===")
if __name__ == "__main__":
    if not Path(DB).exists():
        print(f"NOTICE: DB '{DB}' not found; script will create it at this path.")
    asyncio.run(main())
