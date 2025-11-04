import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import sqlite3
import re
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "competitor_tracker.db"      
SENDER_EMAIL = "techierookies0105@gmail.com"
SENDER_PASSWORD = "dydmzgsxqtmvpdkb"  
RECEIVER_EMAIL = "chaturiya06@gmail.com"
HEADLESS = True
PLAYWRIGHT_TIMEOUT_MS = 20000
SLIGHT_THRESHOLD = 0.005   
MIN_ABS_CHANGE = 1.0       
MODELS_ONLY = ["iPhone 15", "iPhone 16", "iPhone 17"]
def open_conn():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found at {DB_PATH}")
    return sqlite3.connect(str(DB_PATH))

def table_exists(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,))
    return cur.fetchone() is not None

def get_targets_from_db(conn):
    cur = conn.cursor()
    if MODELS_ONLY:
        placeholders = ",".join("?" for _ in MODELS_ONLY)
        sql = f"SELECT DISTINCT model, site, url FROM raw_scrapes WHERE url IS NOT NULL AND model IN ({placeholders})"
        cur.execute(sql, tuple(MODELS_ONLY))
    else:
        cur.execute("SELECT DISTINCT model, site, url FROM raw_scrapes WHERE url IS NOT NULL")
    return cur.fetchall()  # list of tuples (model, site, url)

def get_last_price(conn, model):
    cur = conn.cursor()
    cur.execute("SELECT price FROM dynamic_info WHERE model=? ORDER BY id DESC LIMIT 1", (model,))
    r = cur.fetchone()
    return float(r[0]) if r and r[0] is not None else None

def insert_dynamic_info(conn, model, site, url, price, rating=None, review_count=None):
    cur = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO dynamic_info (model, site, url, price, rating, review_count, extracted_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (model, site, url, price, rating, review_count, ts)
    )
    conn.commit()

def send_email_alert(model, old_price, new_price, url):
    if not (SENDER_EMAIL and SENDER_PASSWORD and RECEIVER_EMAIL):
        print("Email credentials not configured: skipping email alert.")
        return
    subject = f"[Price Alert] {model}: ₹{old_price} -> ₹{new_price}"
    body = f"Model: {model}\nOld price: ₹{old_price}\nNew price: ₹{new_price}\nURL: {url}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(SENDER_EMAIL, SENDER_PASSWORD)
            s.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"Email alert sent for {model}")
    except Exception as e:
        print("Failed sending email:", e)

def extract_price_from_text(text):
    if not text:
        return None
    # look for ₹ or Rs patterns first
    m = re.search(r'(?:₹|Rs\.?)\s*([0-9\.,]+)', text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except:
            pass
    # fallback: largest number
    m2 = re.findall(r'([0-9]{1,3}(?:[,0-9]{3})*(?:\.[0-9]+)?)', text)
    if m2:
        # pick the longest numeric token
        best = max(m2, key=len)
        try:
            return float(best.replace(",", ""))
        except:
            pass
    return None

def extract_rating_and_reviews(text):
    rating = None
    reviews = None
    m = re.search(r'([0-9]\.?[0-9]?)\s*(?:out of|outof)?\s*5', text, re.IGNORECASE)
    if m:
        try:
            rating = float(m.group(1))
        except:
            rating = None
    m2 = re.search(r'([\d,]+)\s*(?:ratings|rating|reviews|review)', text, re.IGNORECASE)
    if m2:
        try:
            reviews = int(m2.group(1).replace(",", ""))
        except:
            reviews = None
    return rating, reviews

# ----------------------------------------

# ----------- Playwright scraping -----------
async def fetch_html_playwright(page, url):
    try:
        await page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS, wait_until="networkidle")
    except PlaywrightTimeoutError:
        try:
            await page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS*2, wait_until="networkidle")
        except Exception as e:
            print("Navigation failed:", e)
            return None
    await asyncio.sleep(0.5)
    try:
        return await page.content()
    except Exception as e:
        print("Could not get page content:", e)
        return None

async def scrape_price_from_page(page, model, site, url):
    html = await fetch_html_playwright(page, url)
    if not html:
        return None, None, None, None
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    # site-specific quick attempts
    price = None
    rating = None
    review_count = None
    try:
        if "amazon." in url:
            # .a-price .a-offscreen often contains price in Amazon product pages
            off = soup.select_one(".a-offscreen")
            if off:
                price = extract_price_from_text(off.get_text(" ", strip=True))
            # rating (a-icon-alt)
            r = soup.select_one(".a-icon-alt")
            if r:
                rating, _ = extract_rating_and_reviews(r.get_text(" ", strip=True))
            # review count
            rc = soup.select_one("#acrCustomerReviewText") or soup.select_one(".a-size-base")
            if rc:
                _, review_count = extract_rating_and_reviews(rc.get_text(" ", strip=True))
        if "flipkart." in url:
            # Flipkart selectors
            p = soup.select_one("div._30jeq3") or soup.select_one("div._25b18c")
            if p:
                price = extract_price_from_text(p.get_text(" ", strip=True))
            r = soup.select_one("div._3LWZlK")
            if r:
                try:
                    rating = float(r.get_text(" ", strip=True))
                except:
                    rating = None
            rc = soup.select_one("span._2_R_DZ")
            if rc:
                m = re.search(r'([\d,]+)', rc.get_text(" ", strip=True))
                if m:
                    review_count = int(m.group(1).replace(",", ""))
    except Exception as e:
        print("Non-fatal parsing error:", e)

    # fallback to whole-text regex if not found
    if price is None:
        price = extract_price_from_text(text)
    if (rating is None) or (review_count is None):
        r, rc = extract_rating_and_reviews(text)
        if rating is None:
            rating = r
        if review_count is None:
            review_count = rc

    return price, rating, review_count, html

# ----------------------------------------

# --------------- Main ---------------------
async def refresh_all():
    print("Starting refresh:", datetime.now().isoformat())
    # open DB
    try:
        conn = open_conn()
    except FileNotFoundError as e:
        print("DB not found:", e)
        return
    # safety checks
    if not table_exists(conn, "raw_scrapes"):
        print("ERROR: raw_scrapes table not found in DB. Aborting.")
        conn.close()
        return
    if not table_exists(conn, "dynamic_info"):
        print("ERROR: dynamic_info table not found in DB. Aborting.")
        conn.close()
        return

    targets = get_targets_from_db(conn)
    if not targets:
        print("No targets found in raw_scrapes. Aborting.")
        conn.close()
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        for (model, site, url) in targets:
            print("Checking:", model, site, url)
            price, rating, review_count, html = await scrape_price_from_page(page, model, site, url)
            if price is None:
                print("Could not extract price for", model)
                continue
            # fetch last price
            try:
                last_price = get_last_price(conn, model)
            except sqlite3.OperationalError as e:
                print("DB error when reading dynamic_info:", e)
                last_price = None

            # decide if change significant
            changed = False
            if last_price is None:
                changed = True
            else:
                # relative change
                rel = abs(price - last_price) / (last_price if last_price != 0 else 1)
                absdiff = abs(price - last_price)
                if rel >= SLIGHT_THRESHOLD or absdiff >= MIN_ABS_CHANGE:
                    changed = True

            # insert new row always (we want history) — but you can change to insert only when changed
            try:
                insert_dynamic_info(conn, model, site, url, price, rating, review_count)
            except Exception as e:
                print("DB insert error:", e)
                continue

            if changed and last_price is not None:
                print(f"Price changed for {model}: {last_price} -> {price}")
                send_email_alert(model, last_price, price, url)
            elif changed and last_price is None:
                print(f"First recorded price for {model}: {price}")
            else:
                print(f"No significant change for {model} (current {price})")

        await browser.close()
    conn.close()
    print("Refresh finished.")

if __name__ == "__main__":
    asyncio.run(refresh_all())
    