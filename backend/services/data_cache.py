"""
File-based caching for scraped Zomato restaurant data.

Stores scraped data as JSON files in the configured cache directory
with a time-to-live (TTL) mechanism to avoid stale data.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from backend.config import settings

# On Vercel, we bundle pre-scraped JSON files in the backend/data folder to bypass IP blocks.
CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"

logger = logging.getLogger(__name__)


def get_cached_data(city: str) -> Optional[list[dict]]:
    """
    Return cached restaurant data if it exists and is fresh.

    Args:
        city: City slug (e.g., 'mumbai').

    Returns:
        List of restaurant dicts from cache, or None if cache
        is missing or stale (older than TTL).
    """
    cache_path = _cache_path(city)
    if not cache_path.exists():
        logger.info(f"No cache file for '{city}'")
        return None

    # Check TTL
    if not os.environ.get("VERCEL"):
        file_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        if file_age_hours > settings.SCRAPE_CACHE_TTL_HOURS:
            logger.info(
                f"Cache for '{city}' is stale "
                f"({file_age_hours:.1f}h > {settings.SCRAPE_CACHE_TTL_HOURS}h TTL)"
            )
            return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} restaurants from cache for '{city}'")
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read cache for '{city}': {e}")
        return None


def save_to_cache(city: str, data: list[dict]) -> None:
    """
    Save scraped restaurant data to a local JSON cache file.
    Skips writing if on Vercel (read-only filesystem).

    Args:
        city: City slug (e.g., 'mumbai').
        data: List of restaurant dicts to cache.
    """
    if os.environ.get("VERCEL"):
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(city)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cached {len(data)} restaurants for '{city}' → {cache_file}")
    except IOError as e:
        logger.error(f"Failed to write cache for '{city}': {e}")


def clear_cache(city: Optional[str] = None) -> None:
    """
    Clear cached data.

    Args:
        city: If given, clear only that city's cache.
              If None, clear all cached city data.
    """
    if city:
        cache_file = _cache_path(city)
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Cleared cache for '{city}'")
    else:
        count = 0
        for f in CACHE_DIR.glob("*_restaurants.json"):
            f.unlink()
            count += 1
        logger.info(f"Cleared all cache files ({count} files)")


def _cache_path(city: str) -> Path:
    """Return the cache file path for a city."""
    return CACHE_DIR / f"{city.lower().replace(' ', '-')}_restaurants.json"
