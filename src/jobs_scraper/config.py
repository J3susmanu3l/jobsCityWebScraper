from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass
class Settings:
    google_maps_api_key: str
    default_city: str = "Denver, CO"
    default_query: str = "restaurants"
    max_results: int = 60
    timeout_seconds: int = 15


def load_settings() -> Settings:
    load_dotenv()
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY is required. Add it to .env (copy from .env.example)."
        )
    if not key.startswith("AIza"):
        raise ValueError(
            "GOOGLE_MAPS_API_KEY does not look like a Google Maps key. "
            "Use a Google Places API key (usually starts with 'AIza')."
        )

    return Settings(
        google_maps_api_key=key,
        default_city=os.getenv("DEFAULT_CITY", "Denver, CO"),
        default_query=os.getenv("DEFAULT_QUERY", "restaurants"),
        max_results=int(os.getenv("MAX_RESULTS", "60")),
        timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
    )

