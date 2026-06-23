"""
Configuration module for the Zomato AI Recommendation System.

Loads environment variables from .env file and provides
a centralized Settings class for all configuration values.
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class Settings:
    """Centralized application settings loaded from environment variables."""

    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

    # Dataset Configuration
    DATASET_NAME: str = "ManikaSaini/zomato-restaurant-recommendation"

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # Filtering
    MAX_CANDIDATES: int = int(os.getenv("MAX_CANDIDATES", "15"))

settings = Settings()
