"""
Extract a listing's price, rating and stock from a retailer product page.

Why the original extractor produced bad data
--------------------------------------------
It scraped search-results pages, where the first price on the page often
belongs to an advert, an accessory or a different storage variant. When its
selectors missed, it fell back to the first "Rs <number>" anywhere in the
text. That is how stored prices ended up as a constant 10,000 or as the price
of a phone case.

This module does three things differently:

1. It reads fixed product pages, one tracked variant per series, so a price
   series always describes the same item.
2. It tries the most stable sources first. Structured data (JSON-LD and
   product meta tags) exists for search engines and changes rarely. CSS class
   names on retail sites are machine-generated and change often, so they are
   the fallback, never the first choice.
3. It never guesses. If no trusted source yields a price, the result says so
   and nothing is stored. Each result records which method produced it, so a
   selector going stale shows up in the run log instead of in the data.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from bs4 import BeautifulSoup

PRICE_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


@dataclass
class ParsedListing:
    price: float | None = None
    mrp: float | None = None
    rating: float | None = None
    review_count: int | None = None
    in_stock: bool | None = None
    title: str | None = None
    method: str | None = None
    blocked: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---- Small helpers ----------------------------------------------------------

def to_number(text) -> float | None:
    """Turn '₹79,900.00' or '79900' into 79900.0, or None."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    match = PRICE_PATTERN.search(str(text).replace("₹", " "))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def to_int(text) -> int | None:
    value = to_number(text)
    return int(value) if value is not None else None


def first_text(soup: BeautifulSoup, selectors: list[str]) -> tuple[str | None, str | None]:
    """Return (text, selector) for the first selector that matches."""
    for selector in selectors:
        element = soup.select_one(selector)
        if element is not None:
            text = element.get_text(" ", strip=True)
            if text:
                return text, selector
    return None, None


def json_ld_products(soup: BeautifulSoup) -> list[dict]:
    """Every schema.org Product object embedded in the page."""
    products: list[dict] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        stack = payload if isinstance(payload, list) else [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            if "@graph" in node:
                stack.extend(node["@graph"] if isinstance(node["@graph"], list) else [node["@graph"]])
            kind = node.get("@type")
            kinds = kind if isinstance(kind, list) else [kind]
            if "Product" in kinds:
                products.append(node)
    return products


def from_json_ld(soup: BeautifulSoup, listing: ParsedListing) -> bool:
    """Fill the listing from schema.org Product data. True if a price was found."""
    for product in json_ld_products(soup):
        offers = product.get("offers")
        offers = offers if isinstance(offers, list) else [offers] if offers else []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            price = to_number(offer.get("price") or offer.get("lowPrice"))
            if price is None:
                continue
            listing.price = price
            availability = str(offer.get("availability", "")).lower()
            if availability:
                listing.in_stock = "instock" in availability or "in_stock" in availability
            listing.title = listing.title or product.get("name")
            rating = product.get("aggregateRating") or {}
            if isinstance(rating, dict):
                listing.rating = to_number(rating.get("ratingValue"))
                listing.review_count = to_int(
                    rating.get("reviewCount") or rating.get("ratingCount")
                )
            listing.method = "json-ld"
            return True
    return False


def from_meta(soup: BeautifulSoup, listing: ParsedListing) -> bool:
    """Open Graph / product meta tags, used by some product pages."""
    for name in ("product:price:amount", "og:price:amount", "twitter:data1"):
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.get("content"):
            price = to_number(tag["content"])
            if price:
                listing.price = price
                listing.method = f"meta:{name}"
                return True
    return False


# ---- Block pages ------------------------------------------------------------

BLOCK_MARKERS = (
    "enter the characters you see below",
    "/errors/validatecaptcha",
    "to discuss automated access to amazon data",
    "api-services-support@amazon.com",
    "are you a human",
    "unusual traffic",
    "recaptcha",
    "access denied",
)


def looks_blocked(html: str) -> bool:
    """True when the page is a bot challenge rather than a product page.

    The collector backs off when it sees one. It deliberately does not try to
    solve or get around challenges: a site that is asking automated clients to
    stop is answered by stopping.
    """
    lowered = html[:200_000].lower()
    return any(marker in lowered for marker in BLOCK_MARKERS)


# ---- Retailer parsers -------------------------------------------------------

# Ordered most stable first. Amazon's ids have been steady for years; its
# class-only selectors are a last resort.
AMAZON_PRICE = [
    "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
    "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
    "#corePrice_feature_div .a-price .a-offscreen",
    "#corePrice_desktop .a-price .a-offscreen",
    "#apex_desktop .a-price .a-offscreen",
    "#priceblock_dealprice",
    "#priceblock_ourprice",
    "#tp_price_block_total_price_ww .a-offscreen",
    "#corePriceDisplay_desktop_feature_div .a-price-whole",
]
AMAZON_MRP = [
    "#corePriceDisplay_desktop_feature_div .basisPrice .a-offscreen",
    "#corePrice_desktop .a-text-price .a-offscreen",
    ".basisPrice .a-offscreen",
]
AMAZON_TITLE = ["#productTitle", "#title"]
AMAZON_RATING = ["#acrPopover .a-icon-alt", "#averageCustomerReviews .a-icon-alt", "span.a-icon-alt"]
AMAZON_REVIEWS = ["#acrCustomerReviewText"]
AMAZON_STOCK = ["#availability", "#outOfStock"]

# Flipkart's class names are generated and rotate. Both the current names and
# the previous generation are listed, newest first; when a run logs
# "no price found" for Flipkart, this list is the first thing to update.
FLIPKART_PRICE = ["div.Nx9bqj.CxhGGd", "div.Nx9bqj", "div._30jeq3._16Jk6d", "div._30jeq3"]
FLIPKART_MRP = ["div.yRaY8j.A6\\+E6v", "div.yRaY8j", "div._3I9_wc._2p6lqe", "div._3I9_wc"]
FLIPKART_TITLE = ["span.VU-ZEz", "h1 span.B_NuCI", "span.B_NuCI", "h1"]
FLIPKART_RATING = ["div.XQDdHH", "div._3LWZlK"]
FLIPKART_REVIEWS = ["span.Wphh3N", "span._2_R_DZ"]
FLIPKART_SOLD_OUT = ["div.Z8JjpR", "div._16FRp0"]


def parse_amazon(html: str) -> ParsedListing:
    listing = ParsedListing()
    if looks_blocked(html):
        listing.blocked = True
        listing.notes.append("bot challenge page")
        return listing

    soup = BeautifulSoup(html, "html.parser")
    listing.title, _ = first_text(soup, AMAZON_TITLE)

    if not (from_json_ld(soup, listing) or from_meta(soup, listing)):
        text, selector = first_text(soup, AMAZON_PRICE)
        if text:
            listing.price = to_number(text)
            listing.method = f"css:{selector}"

    mrp_text, _ = first_text(soup, AMAZON_MRP)
    listing.mrp = to_number(mrp_text)

    if listing.rating is None:
        rating_text, _ = first_text(soup, AMAZON_RATING)
        # "4.5 out of 5 stars" -> 4.5
        listing.rating = to_number(rating_text.split(" out of")[0]) if rating_text else None
    if listing.review_count is None:
        reviews_text, _ = first_text(soup, AMAZON_REVIEWS)
        listing.review_count = to_int(reviews_text)

    if listing.in_stock is None:
        stock_text, _ = first_text(soup, AMAZON_STOCK)
        if stock_text:
            lowered = stock_text.lower()
            listing.in_stock = not ("unavailable" in lowered or "out of stock" in lowered)

    if listing.price is None:
        listing.notes.append("no price found by structured data or selectors")
    return listing


def parse_flipkart(html: str) -> ParsedListing:
    listing = ParsedListing()
    if looks_blocked(html):
        listing.blocked = True
        listing.notes.append("bot challenge page")
        return listing

    soup = BeautifulSoup(html, "html.parser")
    title, _ = first_text(soup, FLIPKART_TITLE)
    listing.title = title

    if not (from_json_ld(soup, listing) or from_meta(soup, listing)):
        text, selector = first_text(soup, FLIPKART_PRICE)
        if text:
            listing.price = to_number(text)
            listing.method = f"css:{selector}"

    mrp_text, _ = first_text(soup, FLIPKART_MRP)
    listing.mrp = to_number(mrp_text)

    if listing.rating is None:
        rating_text, _ = first_text(soup, FLIPKART_RATING)
        listing.rating = to_number(rating_text)
    if listing.review_count is None:
        reviews_text, _ = first_text(soup, FLIPKART_REVIEWS)
        # "1,23,456 Ratings & 5,678 Reviews" -> 5678 reviews when present
        if reviews_text:
            match = re.search(r"([\d,]+)\s*Reviews", reviews_text, flags=re.I)
            listing.review_count = to_int(match.group(1) if match else reviews_text)

    if listing.in_stock is None:
        sold_out, _ = first_text(soup, FLIPKART_SOLD_OUT)
        listing.in_stock = not (sold_out and "sold out" in sold_out.lower())

    if listing.price is None:
        listing.notes.append("no price found by structured data or selectors")
    return listing


PARSERS = {"Amazon": parse_amazon, "Flipkart": parse_flipkart}


def parse(source: str, html: str) -> ParsedListing:
    try:
        return PARSERS[source](html)
    except KeyError as error:
        raise ValueError(f"No parser for retailer '{source}'") from error
