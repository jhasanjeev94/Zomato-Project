import pandas as pd
from backend.models.schemas import UserPreferences

def build_recommendation_prompt(
    prefs: UserPreferences,
    candidates: pd.DataFrame
) -> tuple[str, str]:
    """Build system and user prompts for the LLM."""

    system_prompt = """You are an expert restaurant recommendation assistant. 
Given a list of restaurants and user preferences, analyze each option and 
recommend the top 5 restaurants. For each recommendation, provide a clear, 
compelling explanation of why it's a great fit for the user.

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "...",
      "cuisine": "...",
      "rating": 4.5,
      "estimated_cost": "₹... for two",
      "explanation": "..."
    }
  ],
  "summary": "A brief overall summary of the recommendations"
}"""

    # Format restaurant data as a numbered list
    restaurant_list = []
    for i, (_, row) in enumerate(candidates.iterrows(), 1):
        restaurant_list.append(
            f"{i}. {row['name']} | Cuisine: {row['cuisines']} | "
            f"Rating: {row['aggregate_rating']}/5 | "
            f"Cost: ₹{row['average_cost_for_two']} for two | "
            f"Votes: {row['votes']}"
        )

    restaurants_text = "\n".join(restaurant_list)

    user_prompt = f"""User Preferences:
- Location: {prefs.location}
- Budget: {prefs.budget}
- Cuisine: {prefs.cuisine or "Any"}
- Minimum Rating: {prefs.min_rating}
- Additional: {prefs.additional_preferences or "None"}

Available Restaurants:
{restaurants_text}

Please recommend the top 5 restaurants from this list and explain your reasoning."""

    return system_prompt, user_prompt
