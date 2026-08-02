"""
FastAPI application for the Zomato AI Recommendation System.

Provides REST API endpoints for:
    - Restaurant recommendations (powered by Groq LLM)
    - City/location/cuisine listings
    - Manual scrape refresh
    - Health checks and statistics
"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.models.schemas import UserPreferences, RecommendationResponse
from backend.services.data_loader import (
    load_restaurant_data,
    get_unique_cities,
    get_unique_locations,
    get_unique_cuisines,
    get_dataset_stats,
    clear_memory_cache,
)
from backend.services.data_cache import clear_cache
from backend.services.filter_engine import filter_restaurants
from backend.services.prompt_builder import build_recommendation_prompt
from backend.services.llm_client import groq_client

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: preload default city (Mumbai) data."""
    load_restaurant_data("mumbai")
    yield


app = FastAPI(
    title="Zomato AI Recommendation API",
    description="AI-powered restaurant recommendations using live Zomato data",
    version="2.0.0",
    lifespan=lifespan,
)

# Build allowed origins — production Vercel URL + local dev origins
_allowed_origins = [
    "https://zomato-project-psi.vercel.app",  # Vercel frontend
    "http://localhost:5500",   # VS Code Live Server
    "http://localhost:8000",   # FastAPI static serving
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
]
if FRONTEND_URL:
    _allowed_origins.insert(0, FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins if FRONTEND_URL else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "message": str(exc)},
    )


# ── Health & Info ──

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "data_source": "zomato.com (live scraping)"}


@app.get("/api/cities")
async def list_cities():
    """List all supported cities."""
    return {"cities": get_unique_cities()}


@app.get("/api/locations/{city}")
async def list_locations(city: str):
    """List all known localities in a given city."""
    return {"locations": get_unique_locations(city)}


@app.get("/api/cuisines/{city}")
async def list_cuisines(city: str):
    """List all known cuisines in a given city."""
    return {"cuisines": get_unique_cuisines(city)}


@app.get("/api/stats/{city}")
async def dataset_stats(city: str):
    """Get dataset statistics for a city."""
    stats = get_dataset_stats(city)
    if stats["total_restaurants"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for city: {city}. Try scraping first.",
        )
    return stats


# ── Scraping ──

@app.post("/api/scrape/{city}")
async def force_scrape(city: str):
    """
    Force re-scrape of restaurant data for a city.

    Clears both file and in-memory caches, then scrapes fresh data.
    """
    clear_cache(city)
    clear_memory_cache(city)
    df = load_restaurant_data(city)
    return {
        "message": f"Scraped {len(df)} restaurants for {city}",
        "total_restaurants": len(df),
    }


# ── Recommendations ──

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(prefs: UserPreferences):
    """
    Get AI-powered restaurant recommendations.

    1. Loads restaurant data for the requested city (cached or scraped)
    2. Applies deterministic filters based on user preferences
    3. Sends filtered candidates to Groq LLM for ranking
    4. Returns structured recommendations with explanations
    """
    df = load_restaurant_data(prefs.city)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No restaurant data available for '{prefs.city}'. Try scraping first.",
        )

    candidates = filter_restaurants(df, prefs)

    if candidates.empty:
        raise HTTPException(
            status_code=404,
            detail="No restaurants found matching your preferences. Try relaxing your filters.",
        )

    system_prompt, user_prompt = build_recommendation_prompt(prefs, candidates)
    result = groq_client.get_recommendations(system_prompt, user_prompt)

    return RecommendationResponse(
        query=prefs,
        recommendations=result.get("recommendations", []),
        total_matches=len(candidates),
        ai_summary=result.get("summary", ""),
    )


# ── Legacy endpoints (backward compatibility) ──

@app.get("/api/locations")
async def list_locations_default():
    """Legacy: list locations for the default city (Mumbai)."""
    return {"locations": get_unique_locations("mumbai")}


@app.get("/api/cuisines")
async def list_cuisines_default():
    """Legacy: list cuisines for the default city (Mumbai)."""
    return {"cuisines": get_unique_cuisines("mumbai")}


@app.get("/api/stats")
async def dataset_stats_default():
    """Legacy: get stats for the default city (Mumbai)."""
    return get_dataset_stats("mumbai")


# ── Serve frontend ──

@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static files (CSS, JS) — must be AFTER API routes
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
