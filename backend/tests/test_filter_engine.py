import pandas as pd
import pytest
from backend.models.schemas import UserPreferences
from backend.services.filter_engine import filter_restaurants

@pytest.fixture
def sample_df():
    data = {
        "name": ["Rest A", "Rest B", "Rest C", "Rest D", "Rest E"],
        "location": ["Bangalore", "Bangalore", "Delhi", "Bangalore", "Bangalore"],
        "budget_category": ["medium", "low", "medium", "medium", "high"],
        "cuisines": ["italian, cafe", "north indian", "italian", "chinese", "italian"],
        "aggregate_rating": [4.5, 4.0, 4.8, 3.8, 4.2],
        "votes": [100, 50, 200, 30, 150]
    }
    return pd.DataFrame(data)

def test_filter_location_and_budget(sample_df):
    prefs = UserPreferences(
        location="bangalore",
        budget="medium",
        min_rating=0.0
    )
    result = filter_restaurants(sample_df, prefs)
    assert len(result) == 2
    assert "Rest A" in result["name"].values
    assert "Rest D" in result["name"].values

def test_filter_cuisine_partial_match(sample_df):
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=0.0
    )
    result = filter_restaurants(sample_df, prefs)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Rest A"

def test_filter_min_rating(sample_df):
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        min_rating=4.0
    )
    result = filter_restaurants(sample_df, prefs)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Rest A"

def test_sorting_by_rating_and_votes(sample_df):
    # Add another restaurant with same rating to test votes sorting
    new_row = pd.DataFrame({
        "name": ["Rest F"],
        "location": ["Bangalore"],
        "budget_category": ["medium"],
        "cuisines": ["italian"],
        "aggregate_rating": [4.5], # Same rating as Rest A
        "votes": [150] # Higher votes than Rest A
    })
    df = pd.concat([sample_df, new_row], ignore_index=True)
    
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        min_rating=0.0
    )
    result = filter_restaurants(df, prefs)
    assert len(result) == 3
    # Rest F should be first because it has same rating but higher votes than Rest A
    assert result.iloc[0]["name"] == "Rest F"
    assert result.iloc[1]["name"] == "Rest A"
    assert result.iloc[2]["name"] == "Rest D"
