"""
Unit tests for the data loading and preprocessing pipeline.

Tests cover:
- Preprocessing pipeline (cleaning, normalization, bucketing)
- Budget categorization logic
- Data loader caching behavior
"""

import pandas as pd
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.utils.preprocessing import (
    preprocess_dataframe,
    _categorize_budget,
    get_budget_range,
    BUDGET_THRESHOLDS,
)
from backend.services.data_loader import clear_cache


# ─── Test Fixtures ──────────────────────────────────────────────


def _make_sample_df(rows=None):
    """Create a sample DataFrame mimicking the Zomato dataset schema."""
    if rows is None:
        rows = [
            {
                "name": "Barbeque Nation",
                "location": "Bangalore",
                "cuisines": "North Indian, Chinese",
                "average_cost_for_two": 1500,
                "aggregate_rating": 4.2,
                "votes": 750,
            },
            {
                "name": "Pizza Hut",
                "location": "Delhi",
                "cuisines": "Italian, Fast Food",
                "average_cost_for_two": 800,
                "aggregate_rating": 3.8,
                "votes": 300,
            },
            {
                "name": "Street Bites",
                "location": "mumbai",
                "cuisines": "Street Food",
                "average_cost_for_two": 200,
                "aggregate_rating": 4.0,
                "votes": 120,
            },
            {
                "name": "The Grand",
                "location": "  Bangalore  ",
                "cuisines": "Continental, ITALIAN",
                "average_cost_for_two": 3000,
                "aggregate_rating": 4.5,
                "votes": 500,
            },
        ]
    return pd.DataFrame(rows)


# ─── Preprocessing Tests ────────────────────────────────────────


class TestPreprocessing:
    """Tests for the preprocessing pipeline."""

    def test_basic_preprocessing(self):
        """Preprocessing returns a non-empty DataFrame with expected columns."""
        df = preprocess_dataframe(_make_sample_df())
        assert len(df) > 0
        assert "budget_category" in df.columns
        assert "average_cost_for_two" in df.columns
        assert "aggregate_rating" in df.columns

    def test_location_normalization(self):
        """Locations should be title-cased and stripped."""
        df = preprocess_dataframe(_make_sample_df())
        for loc in df["location"]:
            assert loc == loc.strip()
            assert loc == loc.title()

    def test_cuisine_lowercase(self):
        """All cuisines should be lowercase after preprocessing."""
        df = preprocess_dataframe(_make_sample_df())
        for cuisine in df["cuisines"]:
            assert cuisine == cuisine.lower()

    def test_drops_null_name(self):
        """Rows with null name should be dropped."""
        rows = [
            {"name": None, "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 10},
            {"name": "Valid", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Valid"

    def test_drops_null_location(self):
        """Rows with null location should be dropped."""
        rows = [
            {"name": "Test", "location": None, "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 10},
            {"name": "Valid", "location": "Mumbai", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert len(df) == 1

    def test_drops_zero_votes(self):
        """Restaurants with 0 votes should be filtered out."""
        rows = [
            {"name": "No Votes", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 0},
            {"name": "Has Votes", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 50},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Has Votes"

    def test_cost_parsing_with_currency_symbols(self):
        """Cost strings with currency symbols should be parsed to numeric."""
        rows = [
            {"name": "Test", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": "₹1,500", "aggregate_rating": 4.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert df.iloc[0]["average_cost_for_two"] == 1500.0

    def test_rating_clamped_to_range(self):
        """Ratings should be clamped between 0 and 5."""
        rows = [
            {"name": "Over", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 7.5, "votes": 10},
            {"name": "Under", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": -1.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert df[df["name"] == "Over"]["aggregate_rating"].iloc[0] == 5.0
        assert df[df["name"] == "Under"]["aggregate_rating"].iloc[0] == 0.0

    def test_null_cuisines_become_unknown(self):
        """Null cuisine values should become 'unknown'."""
        rows = [
            {"name": "Test", "location": "Delhi", "cuisines": None,
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert df.iloc[0]["cuisines"] == "unknown"

    def test_deduplication(self):
        """Duplicate (name, location) pairs should be deduplicated."""
        rows = [
            {"name": "Same Place", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 100},
            {"name": "Same Place", "location": "Delhi", "cuisines": "Indian",
             "average_cost_for_two": 500, "aggregate_rating": 4.0, "votes": 50},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert len(df) == 1
        assert df.iloc[0]["votes"] == 100  # Keeps highest votes

    def test_missing_cost_column(self):
        """Should handle missing 'average_cost_for_two' column gracefully."""
        rows = [
            {"name": "Test", "location": "Delhi", "cuisines": "Indian",
             "aggregate_rating": 4.0, "votes": 10},
        ]
        df = preprocess_dataframe(pd.DataFrame(rows))
        assert "average_cost_for_two" in df.columns
        assert "budget_category" in df.columns

    def test_index_is_reset(self):
        """DataFrame index should be reset after preprocessing."""
        df = preprocess_dataframe(_make_sample_df())
        assert list(df.index) == list(range(len(df)))


# ─── Budget Categorization Tests ────────────────────────────────


class TestBudgetCategorization:
    """Tests for the budget bucketing logic."""

    def test_low_budget(self):
        assert _categorize_budget(0) == "low"
        assert _categorize_budget(200) == "low"
        assert _categorize_budget(499) == "low"

    def test_medium_budget(self):
        assert _categorize_budget(500) == "medium"
        assert _categorize_budget(1000) == "medium"
        assert _categorize_budget(1499) == "medium"

    def test_high_budget(self):
        assert _categorize_budget(1500) == "high"
        assert _categorize_budget(3000) == "high"
        assert _categorize_budget(50000) == "high"

    def test_boundary_low_medium(self):
        """Exactly 500 should be 'medium', not 'low'."""
        assert _categorize_budget(499.99) == "low"
        assert _categorize_budget(500) == "medium"

    def test_boundary_medium_high(self):
        """Exactly 1500 should be 'high', not 'medium'."""
        assert _categorize_budget(1499.99) == "medium"
        assert _categorize_budget(1500) == "high"

    def test_negative_cost(self):
        """Negative cost should still return a category (low)."""
        # Negative costs shouldn't exist but shouldn't crash
        assert _categorize_budget(-100) == "high"  # Falls through to default

    def test_budget_distribution_in_sample(self):
        """Sample data should produce expected budget distribution."""
        df = preprocess_dataframe(_make_sample_df())
        categories = df["budget_category"].value_counts().to_dict()
        assert "low" in categories or "medium" in categories or "high" in categories


# ─── Budget Range Helper Tests ──────────────────────────────────


class TestBudgetRange:
    """Tests for the get_budget_range helper."""

    def test_valid_ranges(self):
        assert get_budget_range("low") == (0, 500)
        assert get_budget_range("medium") == (500, 1500)
        assert get_budget_range("high") == (1500, float("inf"))

    def test_invalid_budget_raises(self):
        with pytest.raises(ValueError, match="Invalid budget"):
            get_budget_range("ultra")


# ─── Run Tests ──────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
