"""
Zomato web scraper — extracts restaurant data from zomato.com.

Uses JSON-LD structured data embedded in Zomato's HTML pages
for reliable, structured extraction. Includes rate limiting
and browser-like headers to be a polite scraper.
"""

import json
import time
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from backend.config import settings

logger = logging.getLogger(__name__)

# Browser-like headers to avoid being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Rate limiting: minimum delay between requests (seconds)
REQUEST_DELAY_SECONDS = 2


def scrape_city_restaurants(
    city: str,
    max_pages: Optional[int] = None,
) -> list[dict]:
    """
    Scrape restaurant listings from Zomato for a given city.

    Fetches multiple pages of the restaurant listing and extracts
    structured data from JSON-LD tags embedded in the HTML.

    Args:
        city: City slug (e.g., 'mumbai', 'delhi-ncr').
        max_pages: Maximum number of pages to scrape. Defaults to config value.

    Returns:
        List of restaurant dictionaries.
    """
    if max_pages is None:
        max_pages = settings.MAX_PAGES_PER_CITY

    all_restaurants: list[dict] = []

    for page in range(1, max_pages + 1):
        url = f"{settings.ZOMATO_BASE_URL}/{city}/restaurants?page={page}"
        logger.info(f"Scraping page {page}/{max_pages}: {url}")

        restaurants = _scrape_page(url, city)

        if not restaurants:
            logger.info(f"No restaurants found on page {page}. Stopping.")
            break

        all_restaurants.extend(restaurants)
        logger.info(f"Page {page}: extracted {len(restaurants)} restaurants")

        # Rate limit — be polite to Zomato's servers
        if page < max_pages:
            time.sleep(REQUEST_DELAY_SECONDS)

    unique = _deduplicate(all_restaurants)
    logger.info(
        f"Scraping complete for '{city}': "
        f"{len(unique)} unique restaurants from {page} pages"
    )
    return unique


def _scrape_page(url: str, city: str) -> list[dict]:
    """
    Scrape a single page and extract restaurant data from JSON-LD.

    Args:
        url: Full URL of the Zomato listing page.
        city: City slug for metadata.

    Returns:
        List of restaurant dicts extracted from this page.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    restaurants: list[dict] = []

    # Extract from JSON-LD structured data (schema.org)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "ItemList":
                for item in data.get("itemListElement", []):
                    restaurant = item.get("item", {})
                    if restaurant.get("@type") == "Restaurant":
                        parsed = _parse_jsonld_restaurant(restaurant, city)
                        if parsed:
                            restaurants.append(parsed)
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    return restaurants


def _parse_jsonld_restaurant(data: dict, city: str) -> Optional[dict]:
    """
    Parse a single restaurant entry from JSON-LD schema.

    Fields extracted:
        - name, city, location, address, cuisines
        - aggregate_rating, votes (reviewCount)
        - image_url, zomato_url
        - average_cost_for_two (defaults to 0 — enriched later)

    Args:
        data: JSON-LD restaurant object.
        city: City slug.

    Returns:
        Parsed restaurant dict, or None if parsing fails.
    """
    try:
        rating_data = data.get("aggregateRating", {})
        address_data = data.get("address", {})

        name = data.get("name", "").strip()
        if not name:
            return None

        return {
            "name": name,
            "city": city.replace("-", " ").title(),
            "location": _extract_location_from_url(data.get("url", ""), city),
            "address": address_data.get("streetAddress", "").strip(),
            "cuisines": data.get("servesCuisine", "").strip(),
            "aggregate_rating": float(rating_data.get("ratingValue", 0)),
            "votes": int(rating_data.get("reviewCount", 0)),
            "image_url": data.get("image", ""),
            "zomato_url": settings.ZOMATO_BASE_URL + data.get("url", ""),
            "average_cost_for_two": 0,  # Not available in listing JSON-LD
        }
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse restaurant: {e}")
        return None


def _extract_location_from_url(url: str, city: str) -> str:
    """
    Extract locality name from a Zomato restaurant URL slug.

    Zomato URLs follow the pattern:
        /{city}/{restaurant-name-locality}/info

    Example:
        '/mumbai/tanatan-dadar-shivaji-park/info'
        → 'Dadar Shivaji Park'

    Args:
        url: Relative restaurant URL from JSON-LD.
        city: City slug to strip from the URL.

    Returns:
        Best-effort locality name, or 'Unknown'.
    """
    if not url:
        return "Unknown"

    # Remove leading/trailing slashes, split into parts
    parts = url.strip("/").split("/")
    if len(parts) < 2:
        return "Unknown"

    # The restaurant slug is the second part (after city)
    slug = parts[1]

    # Remove '/info' suffix if present
    slug = slug.replace("/info", "")

    # Split slug by hyphens
    segments = slug.split("-")

    if len(segments) <= 2:
        return segments[-1].title() if segments else "Unknown"

    # Heuristic: the restaurant name usually comes first,
    # and the locality is the last 2-3 segments.
    # For better accuracy, take the last 2 segments.
    locality = " ".join(segments[-2:]).title()
    return locality


def _deduplicate(restaurants: list[dict]) -> list[dict]:
    """
    Remove duplicate restaurants by (name, city) key.

    Keeps the first occurrence (which typically has the
    most data from earlier pages).

    Args:
        restaurants: List of restaurant dicts.

    Returns:
        Deduplicated list.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for r in restaurants:
        key = (r["name"].lower().strip(), r["city"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique
