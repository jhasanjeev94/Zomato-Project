"""
Prompt builder for the Groq LLM recommendation engine.

Constructs system and user prompts from user preferences
and filtered restaurant candidates.
"""

import pandas as pd
from backend.models.schemas import UserPreferences


def build_recommendation_prompt(
    prefs: UserPreferences,
    candidates: pd.DataFrame
) -> tuple[str, str]:
    """
    Build system and user prompts for the LLM.

    The system prompt defines the AI's role and required JSON output format.
    The user prompt provides the user's preferences and candidate restaurants.

    Args:
        prefs: User's preference criteria.
        candidates: Filtered DataFrame of restaurant candidates.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """

    system_prompt = """You are an expert restaurant recommendation assistant.
Given a list of restaurants scraped from Zomato and user preferences, analyze
each option and recommend the top 5 restaurants. For each recommendation,
provide a clear, compelling explanation of why it's a great fit for the user.

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "...",
      "cuisine": "...",
      "rating": 4.5,
      "estimated_cost": "₹... for two",
      "explanation": "...",
      "image_url": "...",
      "zomato_url": "..."
    }
  ],
  "summary": "A brief overall summary of the recommendations"
}"""

    # Format restaurant data as a numbered list
    restaurant_list = []
    for i, (_, row) in enumerate(candidates.iterrows(), 1):
        cost_str = (
            f"₹{int(row['average_cost_for_two'])} for two"
            if row.get("average_cost_for_two", 0) > 0
            else "Price N/A"
        )
        restaurant_list.append(
            f"{i}. {row['name']} | Cuisine: {row['cuisines']} | "
            f"Rating: {row['aggregate_rating']}/5 | "
            f"Cost: {cost_str} | "
            f"Votes: {row['votes']} | "
            f"Location: {row.get('location', 'N/A')} | "
            f"Image: {row.get('image_url', '')} | "
            f"URL: {row.get('zomato_url', '')}"
        )

    restaurants_text = "\n".join(restaurant_list)

    user_prompt = f"""User Preferences:
- City: {prefs.city}
- Location: {prefs.location or "Any"}
- Budget: {prefs.budget}
- Cuisine: {prefs.cuisine or "Any"}
- Minimum Rating: {prefs.min_rating}
- Additional: {prefs.additional_preferences or "None"}

Available Restaurants (from live Zomato data):
{restaurants_text}

Please recommend the top 5 restaurants from this list and explain your reasoning."""

    return system_prompt, user_prompt
