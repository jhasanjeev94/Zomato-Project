"""
Data loading service for the Zomato restaurant recommendation system.

Uses a cache-first strategy:
    1. In-memory cache (fastest)
    2. File cache (JSON on disk with TTL)
    3. Live scrape from Zomato (last resort)
"""

import logging
from typing import Optional

import pandas as pd

from backend.services.scraper import scrape_city_restaurants
from backend.services.data_cache import get_cached_data, save_to_cache
from backend.utils.preprocessing import preprocess_dataframe
from backend.config import settings

logger = logging.getLogger(__name__)

# In-memory cache: city → preprocessed DataFrame
_cached_dfs: dict[str, pd.DataFrame] = {}


def load_restaurant_data(city: str = "mumbai") -> pd.DataFrame:
    """
    Load restaurant data with a cache-first strategy.

    Resolution order:
        1. In-memory DataFrame cache
        2. File-based JSON cache (if fresh per TTL)
        3. Live scrape from zomato.com

    Args:
        city: City slug (e.g., 'mumbai', 'delhi-ncr').

    Returns:
        Preprocessed DataFrame of restaurant data.
        Empty DataFrame if no data could be loaded.
    """
    city = city.lower().replace(" ", "-")

    # 1. In-memory cache
    if city in _cached_dfs:
        logger.info(f"Returning in-memory cache for '{city}' ({len(_cached_dfs[city])} rows)")
        return _cached_dfs[city]

    # 2. File cache
    cached = get_cached_data(city)
    if cached:
        df = pd.DataFrame(cached)
        df = preprocess_dataframe(df)
        _cached_dfs[city] = df
        logger.info(f"Loaded from file cache: '{city}' ({len(df)} restaurants)")
        return df

    # 3. Live scrape
    logger.info(f"No cache for '{city}'. Starting live scrape from Zomato...")
    raw_data = scrape_city_restaurants(city, max_pages=settings.MAX_PAGES_PER_CITY)

    if not raw_data:
        logger.warning(f"Scrape returned no data for '{city}'")
        return pd.DataFrame()

    # Save to file cache
    save_to_cache(city, raw_data)

    # Preprocess and cache in memory
    df = pd.DataFrame(raw_data)
    df = preprocess_dataframe(df)
    _cached_dfs[city] = df
    logger.info(f"Scraped and cached: '{city}' ({len(df)} restaurants)")
    return df


def get_unique_cities() -> list[str]:
    """
    Return list of supported cities in display format.

    Returns:
        List of city names in title case.
    """
    return [c.replace("-", " ").title() for c in settings.SUPPORTED_CITIES]


def get_unique_locations(city: str = "mumbai") -> list[str]:
    """
    Return sorted list of all unique locations/localities for a city.

    Args:
        city: City slug.

    Returns:
        Sorted list of location strings.
    """
    df = load_restaurant_data(city)
    if df.empty:
        return []
    return sorted(
        df["location"]
        .dropna()
        .loc[lambda s: s != "Unknown"]
        .unique()
        .tolist()
    )


def get_unique_cuisines(city: str = "mumbai") -> list[str]:
    """
    Return sorted list of all unique individual cuisines for a city.

    Multi-cuisine entries (e.g., "north indian, chinese") are
    split into individual cuisine types.

    Args:
        city: City slug.

    Returns:
        Sorted list of unique cuisine strings.
    """
    df = load_restaurant_data(city)
    if df.empty:
        return []
    all_cuisines = (
        df["cuisines"]
        .str.split(",")
        .explode()
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
    )
    return sorted(all_cuisines.tolist())


def get_dataset_stats(city: str = "mumbai") -> dict:
    """
    Return summary statistics about the loaded dataset for a city.

    Args:
        city: City slug.

    Returns:
        Dictionary with restaurant counts, ratings, and source info.
    """
    df = load_restaurant_data(city)
    if df.empty:
        return {"total_restaurants": 0, "city": city, "data_source": "zomato.com"}
    return {
        "city": city,
        "total_restaurants": len(df),
        "total_locations": df["location"].nunique(),
        "total_cuisines": len(get_unique_cuisines(city)),
        "average_rating": round(df["aggregate_rating"].mean(), 2),
        "data_source": "zomato.com",
    }


def clear_memory_cache(city: Optional[str] = None) -> None:
    """
    Clear the in-memory dataset cache.

    Args:
        city: If given, clear only that city. If None, clear all.
    """
    global _cached_dfs
    if city:
        city = city.lower().replace(" ", "-")
        _cached_dfs.pop(city, None)
        logger.info(f"Cleared in-memory cache for '{city}'")
    else:
        _cached_dfs.clear()
        logger.info("Cleared all in-memory caches")
