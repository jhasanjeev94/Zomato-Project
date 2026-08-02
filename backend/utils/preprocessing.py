"""
Data preprocessing utilities for Zomato restaurant data.

Handles cleaning, normalization, and budget bucketing
of scraped restaurant data from zomato.com.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Budget thresholds (average cost for two in INR)
BUDGET_THRESHOLDS = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, float("inf")),
}


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize scraped Zomato restaurant data.

    Pipeline:
        1. Drop rows with missing name
        2. Normalize cuisine strings (lowercase, strip)
        3. Parse cost to numeric
        4. Bucket cost into low/medium/high categories
        5. Ensure rating is numeric (clamped 0-5)
        6. Ensure votes is numeric
        7. Normalize location and city strings
        8. Deduplicate by (name, city)

    Args:
        df: Raw DataFrame from scraper or JSON cache.

    Returns:
        Cleaned and standardized DataFrame.
    """
    initial_count = len(df)
    logger.info(f"Starting preprocessing with {initial_count} rows")

    # 1. Drop rows with missing name
    df = df.dropna(subset=["name"])
    df = df[df["name"].str.strip() != ""]
    logger.info(f"After dropping empty names: {len(df)} rows")

    df = df.copy()

    # 2. Normalize cuisine strings
    df["cuisines"] = (
        df["cuisines"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # 3. Parse cost to numeric
    if "average_cost_for_two" in df.columns:
        df["average_cost_for_two"] = pd.to_numeric(
            df["average_cost_for_two"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        ).fillna(0)
    else:
        df["average_cost_for_two"] = 0

    # 4. Bucket cost into categories
    df["budget_category"] = df["average_cost_for_two"].apply(_categorize_budget)

    # 5. Ensure rating is numeric and clamped to 0-5
    if "aggregate_rating" in df.columns:
        df["aggregate_rating"] = df["aggregate_rating"].apply(_parse_rating)
    else:
        df["aggregate_rating"] = 0.0

    # Drop rows with NaN ratings
    df = df.dropna(subset=["aggregate_rating"])

    # 6. Ensure votes is numeric
    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
    else:
        df["votes"] = 0

    # 7. Normalize location and city strings
    df["location"] = df["location"].fillna("Unknown").astype(str).str.strip().str.title()
    df["city"] = df["city"].fillna("").astype(str).str.strip().str.title()
    df["name"] = df["name"].astype(str).str.strip()

    # 8. Ensure optional URL/image columns exist
    for col in ["image_url", "zomato_url", "address"]:
        if col not in df.columns:
            df[col] = ""

    # 9. Deduplicate by (name, city) — keep first occurrence
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["name", "city"], keep="first")
    if before_dedup > len(df):
        logger.info(f"Removed {before_dedup - len(df)} duplicate entries")

    df = df.reset_index(drop=True)
    logger.info(f"Preprocessing complete: {len(df)} restaurants ready")

    return df


def _parse_rating(value) -> float:
    """
    Parse rating values to float, clamped between 0 and 5.

    Handles formats:
        - 4.1     → 4.1
        - "4.1/5" → 4.1
        - "NEW"   → NaN
        - None    → NaN

    Args:
        value: Raw rating value.

    Returns:
        Float rating between 0 and 5, or NaN.
    """
    if pd.isna(value):
        return float("nan")

    val_str = str(value).strip()

    # Handle known non-numeric markers
    if val_str.lower() in ("new", "-", "--", "", "nan", "none"):
        return float("nan")

    # Handle "X/5" format
    if "/" in val_str:
        try:
            numerator = val_str.split("/")[0].strip()
            return max(0.0, min(5.0, float(numerator)))
        except (ValueError, IndexError):
            return float("nan")

    # Handle plain numeric
    try:
        return max(0.0, min(5.0, float(val_str)))
    except ValueError:
        return float("nan")


def _categorize_budget(cost: float) -> str:
    """
    Categorize a cost value into a budget tier.

    Args:
        cost: Average cost for two in INR.

    Returns:
        Budget category: 'low', 'medium', or 'high'.
        Defaults to 'medium' if cost is 0 (unknown from listing page).
    """
    if cost <= 0:
        return "medium"  # Unknown cost — default to medium
    for category, (low, high) in BUDGET_THRESHOLDS.items():
        if low <= cost < high:
            return category
    return "high"


def get_budget_range(budget: str) -> tuple[float, float]:
    """
    Get the cost range for a given budget category.

    Args:
        budget: One of 'low', 'medium', 'high'.

    Returns:
        Tuple of (min_cost, max_cost).

    Raises:
        ValueError: If budget is not a valid category.
    """
    if budget not in BUDGET_THRESHOLDS:
        raise ValueError(
            f"Invalid budget '{budget}'. Must be one of: {list(BUDGET_THRESHOLDS.keys())}"
        )
    return BUDGET_THRESHOLDS[budget]
