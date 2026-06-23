from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging

from backend.models.schemas import UserPreferences, RecommendationResponse
from backend.services.data_loader import load_restaurant_data, get_unique_locations, get_unique_cuisines
from backend.services.filter_engine import filter_restaurants
from backend.services.prompt_builder import build_recommendation_prompt
from backend.services.llm_client import groq_client

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload dataset
    load_restaurant_data()
    yield

app = FastAPI(
    title="Zomato AI Recommendation API",
    version="1.0.0",
    lifespan=lifespan,
)

# Build allowed origins — production Vercel URL + local dev origins
_allowed_origins = [
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/locations")
async def list_locations():
    return {"locations": get_unique_locations()}

@app.get("/api/cuisines")
async def list_cuisines():
    return {"cuisines": get_unique_cuisines()}

@app.get("/api/stats")
async def dataset_stats():
    df = load_restaurant_data()
    return {
        "total_restaurants": len(df),
        "total_locations": df["location"].nunique(),
        "total_cuisines": df["cuisines"].nunique(),
        "average_rating": round(df["aggregate_rating"].mean(), 2) if not df.empty else 0.0,
    }

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(prefs: UserPreferences):
    df = load_restaurant_data()
    candidates = filter_restaurants(df, prefs)

    if candidates.empty:
        raise HTTPException(
            status_code=404,
            detail="No restaurants found matching your preferences. Try relaxing your filters."
        )

    system_prompt, user_prompt = build_recommendation_prompt(prefs, candidates)
    result = groq_client.get_recommendations(system_prompt, user_prompt)

    return RecommendationResponse(
        query=prefs,
        recommendations=result.get("recommendations", []),
        total_matches=len(candidates),
        ai_summary=result.get("summary", ""),
    )

# ── Serve frontend ──
@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

# Mount static files (CSS, JS) — must be AFTER API routes
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

