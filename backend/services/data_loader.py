"""
Data loading service for the Zomato restaurant dataset.

Loads the dataset from a bundled local CSV file, preprocesses it,
and caches it in memory for fast access.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.utils.preprocessing import preprocess_dataframe

logger = logging.getLogger(__name__)

# Path to the bundled CSV dataset
_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "zomato_restaurants.csv"

# In-memory cache for the preprocessed DataFrame
_cached_df: Optional[pd.DataFrame] = None


def load_restaurant_data(force_reload: bool = False) -> pd.DataFrame:
    """
    Load and cache the Zomato dataset from the bundled CSV.

    On first call, reads the CSV, preprocesses it,
    and stores it in memory. Subsequent calls return the cached copy.

    Args:
        force_reload: If True, bypass cache and reload from disk.

    Returns:
        Preprocessed DataFrame of restaurant data.

    Raises:
        RuntimeError: If dataset cannot be loaded.
    """
    global _cached_df

    if _cached_df is not None and not force_reload:
        return _cached_df

    try:
        logger.info(f"Loading dataset from: {_DATA_FILE}")
        raw_df = pd.read_csv(_DATA_FILE)
        logger.info(
            f"Raw dataset loaded: {len(raw_df)} rows, "
            f"{len(raw_df.columns)} columns"
        )
        logger.info(f"Columns: {list(raw_df.columns)}")

        _cached_df = preprocess_dataframe(raw_df)

        logger.info(
            f"Dataset ready: {len(_cached_df)} restaurants, "
            f"{_cached_df['location'].nunique()} locations, "
            f"avg rating {_cached_df['aggregate_rating'].mean():.2f}"
        )

        return _cached_df

    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(
            f"Could not load dataset from '{_DATA_FILE}'. "
            f"Error: {e}"
        ) from e


def get_unique_locations() -> list[str]:
    """
    Return a sorted list of all unique restaurant locations.

    Returns:
        List of location strings (title-cased).
    """
    df = load_restaurant_data()
    return sorted(df["location"].unique().tolist())


def get_unique_cuisines() -> list[str]:
    """
    Return a sorted list of all unique individual cuisines.

    Multi-cuisine entries (e.g., "north indian, chinese") are
    split and deduplicated into individual cuisine types.

    Returns:
        Sorted list of unique cuisine strings.
    """
    df = load_restaurant_data()
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


def get_dataset_stats() -> dict:
    """
    Return summary statistics about the loaded dataset.

    Returns:
        Dictionary with total restaurants, locations, cuisines,
        average rating, and budget distribution.
    """
    df = load_restaurant_data()
    return {
        "total_restaurants": len(df),
        "total_locations": df["location"].nunique(),
        "total_cuisines": len(get_unique_cuisines()),
        "average_rating": round(df["aggregate_rating"].mean(), 2),
        "budget_distribution": df["budget_category"].value_counts().to_dict(),
        "top_locations": (
            df["location"]
            .value_counts()
            .head(10)
            .to_dict()
        ),
    }


def clear_cache() -> None:
    """Clear the in-memory dataset cache (useful for testing)."""
    global _cached_df
    _cached_df = None
    logger.info("Dataset cache cleared")
