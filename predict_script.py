import json
from backend.models.schemas import UserPreferences
from backend.services.data_loader import load_restaurant_data
from backend.services.filter_engine import filter_restaurants
from backend.services.prompt_builder import build_recommendation_prompt
from backend.services.llm_client import groq_client
import time

def predict_top5():
    # Budget maps to "high" since 1500 is in the high bracket in preprocessing
    # Or "medium" if the user meant up to 1500. We will use "high" because cost >= 1500 is high.
    # Actually wait, in preprocessing.py: "medium": (500, 1500), "high": (1500, float("inf"))
    # So 1500 is "high". Let's set it to "high".
    
    print("Loading data...")
    start_time = time.time()
    df = load_restaurant_data()
    print(f"Data loaded in {time.time() - start_time:.2f} seconds. Total restaurants: {len(df)}")
    
    prefs = UserPreferences(
        location="Bellandur",
        budget="medium",
        cuisine=None,
        min_rating=4.2
    )
    
    print(f"Filtering data for: Location={prefs.location}, Budget={prefs.budget}, Min Rating={prefs.min_rating}")
    candidates = filter_restaurants(df, prefs)
    print(f"Found {len(candidates)} candidates.")
    
    if len(candidates) == 0:
        print("No candidates found matching the criteria. LLM prediction skipped.")
        return
        
    print("Building prompt...")
    system_prompt, user_prompt = build_recommendation_prompt(prefs, candidates)
    
    print("Calling Groq LLM...")
    try:
        response = groq_client.get_recommendations(system_prompt, user_prompt)
        print("\n=== TOP 5 RESTAURANT PREDICTIONS ===")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print("Error calling Groq API:", e)

if __name__ == "__main__":
    predict_top5()
