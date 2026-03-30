"""
Tool: get_traffic_score
Calls Google Maps Places API (Nearby Search + popularity signals) to estimate
foot-traffic for a given lat/lng.  Falls back to a deterministic synthetic
score when the API key is absent (handy for local dev / demos).
"""

import os
import math
import random
import logging
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synthetic_traffic_score(lat: float, lng: float) -> float:
    """
    Deterministic fallback that produces a plausible 0-100 score based on
    coordinate hashing so the same location always returns the same value.
    """
    seed = int(abs(lat * 1_000) + abs(lng * 1_000)) % 10_000
    rng = random.Random(seed)
    base = rng.uniform(30, 90)
    # Slight bonus for central Almaty coordinates
    if 43.20 <= lat <= 43.28 and 76.88 <= lng <= 76.98:
        base = min(100, base + 10)
    return round(base, 2)


async def _fetch_places_nearby(lat: float, lng: float, radius: int = 500) -> dict:
    """
    Hits the Google Places Nearby Search endpoint.
    Returns the raw JSON response dict.
    """
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "establishment",
        "key": GOOGLE_MAPS_API_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _score_from_places(data: dict) -> float:
    """
    Derives a 0-100 traffic score from the number of nearby establishments
    and their average user-rating count (a proxy for busyness).
    """
    results = data.get("results", [])
    if not results:
        return 20.0

    count = len(results)
    avg_ratings = sum(r.get("user_ratings_total", 0) for r in results) / count

    # Normalise: 50+ places → saturates density at 1.0
    density_score = min(count / 50, 1.0) * 50
    # Normalise: 2000+ aggregate ratings → saturates at 1.0
    rating_score = min(avg_ratings / 2000, 1.0) * 50

    return round(density_score + rating_score, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_traffic_score(lat: float, lng: float) -> dict:
    """
    Returns a dict with:
      - score         : float  0-100
      - source        : 'google_maps' | 'synthetic'
      - nearby_count  : int    (number of establishments within 500 m)
      - explanation   : str
    """
    if not GOOGLE_MAPS_API_KEY:
        score = _synthetic_traffic_score(lat, lng)
        logger.warning("GOOGLE_MAPS_API_KEY not set – using synthetic traffic score.")
        return {
            "score": score,
            "source": "synthetic",
            "nearby_count": None,
            "explanation": (
                f"Synthetic score (no API key). Based on location hash. "
                f"Score: {score}/100."
            ),
        }

    try:
        data = await _fetch_places_nearby(lat, lng)
        score = _score_from_places(data)
        nearby_count = len(data.get("results", []))
        return {
            "score": score,
            "source": "google_maps",
            "nearby_count": nearby_count,
            "explanation": (
                f"Derived from {nearby_count} establishments within 500 m. "
                f"Score: {score}/100."
            ),
        }
    except Exception as exc:
        logger.error("Google Maps API error: %s – falling back to synthetic.", exc)
        score = _synthetic_traffic_score(lat, lng)
        return {
            "score": score,
            "source": "synthetic_fallback",
            "nearby_count": None,
            "explanation": f"API error ({exc}). Fallback synthetic score: {score}/100.",
        }
