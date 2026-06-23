from pydantic import BaseModel, Field
from typing import Optional, Literal

class UserPreferences(BaseModel):
    location: str = Field(..., description="City or area name")
    budget: Literal["low", "medium", "high"] = Field(..., description="Budget category")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine type")
    min_rating: float = Field(3.5, ge=0.0, le=5.0, description="Minimum rating")
    additional_preferences: Optional[str] = Field(None, description="Extra preferences")

class RestaurantRecommendation(BaseModel):
    rank: int
    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str

class RecommendationResponse(BaseModel):
    query: UserPreferences
    recommendations: list[RestaurantRecommendation]
    total_matches: int
    ai_summary: str
