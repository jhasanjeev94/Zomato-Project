"""
Data preprocessing utilities for the Zomato dataset.

Handles cleaning, normalization, column mapping, and budget bucketing
of raw restaurant data from HuggingFace.
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

# Map raw HuggingFace column names → standardized internal names
COLUMN_MAPPING = {
    "name": "name",
    "location": "location",
    "cuisines": "cuisines",
    "rate": "aggregate_rating",
    "votes": "votes",
    "approx_cost(for two people)": "average_cost_for_two",
    "online_order": "has_online_delivery",
    "book_table": "has_table_booking",
    "rest_type": "restaurant_type",
    "url": "url",
    "address": "address",
    "phone": "phone",
    "dish_liked": "dish_liked",
    "reviews_list": "reviews_list",
    "menu_item": "menu_item",
    "listed_in(type)": "listed_in_type",
    "listed_in(city)": "listed_in_city",
}


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the raw Zomato dataset.

    Pipeline:
        1. Rename columns to standardized names
        2. Drop rows with missing critical fields (name, location)
        3. Parse and normalize rating (handle "X/5" format, "NEW", "-")
        4. Normalize cuisine strings (lowercase, strip)
        5. Parse cost to numeric (remove currency symbols)
        6. Bucket cost into low/medium/high categories
        7. Filter out restaurants with 0 votes
        8. Normalize location strings (title case)
        9. Deduplicate by (name, location) keeping highest votes

    Args:
        df: Raw DataFrame from HuggingFace dataset.

    Returns:
        Cleaned and standardized DataFrame.
    """
    initial_count = len(df)
    logger.info(f"Starting preprocessing with {initial_count} rows")

    # 1. Rename columns to standardized names
    rename_map = {k: v for k, v in COLUMN_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    logger.info(f"Renamed columns: {list(rename_map.keys())} → {list(rename_map.values())}")

    # 2. Drop rows with missing critical fields
    critical_cols = [c for c in ["name", "location"] if c in df.columns]
    df = df.dropna(subset=critical_cols)
    logger.info(f"After dropping nulls: {len(df)} rows (removed {initial_count - len(df)})")

    df = df.copy()

    # 3. Parse and normalize rating
    if "aggregate_rating" in df.columns:
        df["aggregate_rating"] = df["aggregate_rating"].apply(_parse_rating)
    else:
        df["aggregate_rating"] = 0.0
        logger.warning("No rating column found. Defaulting to 0.0")

    # Drop rows with invalid/unparseable ratings (NaN after parsing)
    df = df.dropna(subset=["aggregate_rating"])

    # 4. Normalize cuisine strings
    df["cuisines"] = df["cuisines"].fillna("unknown").astype(str).str.strip().str.lower()

    # 5. Parse cost to numeric
    if "average_cost_for_two" in df.columns:
        df["average_cost_for_two"] = pd.to_numeric(
            df["average_cost_for_two"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        ).fillna(0)
    else:
        # Fallback: check for alternate column names
        cost_cols = [c for c in df.columns if "cost" in c.lower()]
        if cost_cols:
            df["average_cost_for_two"] = pd.to_numeric(
                df[cost_cols[0]].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce",
            ).fillna(0)
            logger.info(f"Used alternate cost column: {cost_cols[0]}")
        else:
            df["average_cost_for_two"] = 0
            logger.warning("No cost column found. Defaulting to 0.")

    # 6. Bucket cost into categories
    df["budget_category"] = df["average_cost_for_two"].apply(_categorize_budget)

    # 7. Filter out restaurants with 0 votes
    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
        before_votes = len(df)
        df = df[df["votes"] > 0]
        logger.info(f"After filtering 0-vote restaurants: {len(df)} rows (removed {before_votes - len(df)})")
    else:
        logger.warning("No 'votes' column found. Skipping vote filter.")
        df["votes"] = 0

    # 8. Normalize location
    df["location"] = df["location"].astype(str).str.strip().str.title()

    # 9. Normalize restaurant name
    df["name"] = df["name"].astype(str).str.strip()

    # 10. Normalize boolean columns
    for col in ["has_online_delivery", "has_table_booking"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().map(
                {"yes": True, "no": False, "true": True, "false": False}
            ).fillna(False)

    # 11. Deduplicate by (name, location) — keep highest votes
    before_dedup = len(df)
    df = df.sort_values("votes", ascending=False).drop_duplicates(
        subset=["name", "location"], keep="first"
    )
    if before_dedup > len(df):
        logger.info(f"Removed {before_dedup - len(df)} duplicate entries")

    df = df.reset_index(drop=True)
    logger.info(f"Preprocessing complete: {len(df)} restaurants ready")

    return df


def _parse_rating(value) -> float:
    """
    Parse rating values from the Zomato dataset.

    Handles formats:
        - "4.1/5"  → 4.1
        - "4.1"    → 4.1
        - "NEW"    → NaN (will be dropped)
        - "-"      → NaN (will be dropped)
        - ""       → NaN
        - None     → NaN
        - numeric  → float (clamped to 0-5)

    Args:
        value: Raw rating value from dataset.

    Returns:
        Float rating between 0 and 5, or NaN for unparseable values.
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
    """
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
