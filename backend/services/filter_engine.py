"""
Deterministic filter engine for restaurant candidates.

Applies cascading filters based on user preferences to narrow
down the candidate pool before sending to the LLM.
"""

import pandas as pd
from backend.models.schemas import UserPreferences

MAX_CANDIDATES = 15


def filter_restaurants(df: pd.DataFrame, prefs: UserPreferences) -> pd.DataFrame:
    """
    Apply cascading filters based on user preferences.

    Filter pipeline:
        1. Location filter (optional — partial match within city)
        2. Budget filter (skip if cost data is unknown)
        3. Cuisine filter (partial match, optional)
        4. Minimum rating filter
        5. Sort by rating (desc) then votes (desc)
        6. Return top N candidates

    Args:
        df: Preprocessed DataFrame of restaurants (already filtered to city).
        prefs: User's preference criteria.

    Returns:
        Filtered and sorted DataFrame of top candidates.
    """
    filtered = df.copy()

    # 1. Filter by location within city (optional)
    if prefs.location:
        filtered = filtered[
            filtered["location"].str.lower().str.contains(
                prefs.location.lower(), na=False
            )
        ]

    # 2. Filter by budget category
    # Only apply if we have meaningful cost data (some cost > 0)
    has_cost_data = filtered["average_cost_for_two"].sum() > 0
    if has_cost_data:
        budget_filtered = filtered[filtered["budget_category"] == prefs.budget]
        # If budget filter is too aggressive, skip it
        if not budget_filtered.empty:
            filtered = budget_filtered

    # 3. Filter by cuisine (partial match)
    if prefs.cuisine:
        cuisine_filtered = filtered[
            filtered["cuisines"].str.contains(prefs.cuisine.lower(), na=False)
        ]
        # If cuisine filter leaves results, use them; otherwise keep all
        if not cuisine_filtered.empty:
            filtered = cuisine_filtered

    # 4. Filter by minimum rating
    filtered = filtered[filtered["aggregate_rating"] >= prefs.min_rating]

    # 5. Sort by rating (desc) then votes (desc)
    filtered = filtered.sort_values(
        by=["aggregate_rating", "votes"],
        ascending=[False, False]
    )

    # 6. Return top N candidates
    return filtered.head(MAX_CANDIDATES)
