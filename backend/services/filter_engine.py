import pandas as pd
from backend.models.schemas import UserPreferences

MAX_CANDIDATES = 15

def filter_restaurants(df: pd.DataFrame, prefs: UserPreferences) -> pd.DataFrame:
    """Apply cascading filters based on user preferences."""
    filtered = df.copy()

    # 1. Filter by location (case-insensitive)
    filtered = filtered[
        filtered["location"].str.lower() == prefs.location.lower()
    ]

    # 2. Filter by budget category
    filtered = filtered[filtered["budget_category"] == prefs.budget]

    # 3. Filter by cuisine (partial match)
    if prefs.cuisine:
        filtered = filtered[
            filtered["cuisines"].str.contains(prefs.cuisine.lower(), na=False)
        ]

    # 4. Filter by minimum rating
    filtered = filtered[filtered["aggregate_rating"] >= prefs.min_rating]

    # 5. Sort by rating (desc) then votes (desc)
    filtered = filtered.sort_values(
        by=["aggregate_rating", "votes"],
        ascending=[False, False]
    )

    # 6. Return top N candidates
    return filtered.head(MAX_CANDIDATES)
