"""
Pydantic models for the Zomato AI Recommendation API.

Defines request/response schemas for the recommendation endpoint.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class UserPreferences(BaseModel):
    """User's restaurant preferences for generating recommendations."""
    city: str = Field(..., description="City name (e.g., 'mumbai', 'delhi-ncr')")
    location: Optional[str] = Field(None, description="Specific locality within the city")
    budget: Literal["low", "medium", "high"] = Field(..., description="Budget category")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine type")
    min_rating: float = Field(3.5, ge=0.0, le=5.0, description="Minimum rating")
    additional_preferences: Optional[str] = Field(None, description="Extra preferences")


class RestaurantRecommendation(BaseModel):
    """A single restaurant recommendation from the LLM."""
    rank: int
    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
    image_url: Optional[str] = None
    zomato_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Full response for a recommendation request."""
    query: UserPreferences
    recommendations: list[RestaurantRecommendation]
    total_matches: int
    ai_summary: str
