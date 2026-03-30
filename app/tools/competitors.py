"""
Tool: get_nearby_competitors
Queries the OpenStreetMap Overpass API to find businesses of the same type
within a configurable radius of a given lat/lng.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Maps our internal business-type labels → OSM amenity / shop tags
BUSINESS_TYPE_MAP: dict[str, list[str]] = {
    "coffee_shop": ["cafe", "coffee_shop"],
    "cafe":        ["cafe", "coffee_shop"],
    "restaurant":  ["restaurant", "fast_food", "food_court"],
    "bar":         ["bar", "pub", "biergarten"],
    "gym":         ["gym", "fitness_centre", "sports_centre"],
    "pharmacy":    ["pharmacy", "chemist"],
    "bakery":      ["bakery"],
    "supermarket": ["supermarket", "convenience"],
    "hotel":       ["hotel", "motel", "hostel"],
}

DEFAULT_RADIUS_M = 1_000   # 1 km radius


def _build_query(lat: float, lng: float, osm_types: list[str], radius: int) -> str:
    """Build an Overpass QL query for the given amenity types."""
    amenity_union = "\n  ".join(
        f'node["amenity"="{t}"](around:{radius},{lat},{lng});'
        for t in osm_types
    )
    shop_union = "\n  ".join(
        f'node["shop"="{t}"](around:{radius},{lat},{lng});'
        for t in osm_types
    )
    return f"""
[out:json][timeout:25];
(
  {amenity_union}
  {shop_union}
);
out center;
"""


def _resolve_osm_types(business_type: str) -> list[str]:
    """Normalise business_type to OSM tag values."""
    key = business_type.lower().replace(" ", "_")
    return BUSINESS_TYPE_MAP.get(key, [key])


async def get_nearby_competitors(
    lat: float,
    lng: float,
    business_type: str = "coffee_shop",
    radius: int = DEFAULT_RADIUS_M,
) -> dict:
    """
    Returns a dict with:
      - count          : int   number of competitors found
      - competitors    : list  [{name, lat, lng, type}]
      - competitor_gap : float 0-100 (higher = fewer competitors = better gap)
      - radius_m       : int
      - explanation    : str
    """
    osm_types = _resolve_osm_types(business_type)
    query = _build_query(lat, lng, osm_types, radius)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()

        elements = data.get("elements", [])
        competitors = [
            {
                "name": e.get("tags", {}).get("name", "Unnamed"),
                "lat":  e.get("lat", e.get("center", {}).get("lat")),
                "lng":  e.get("lon", e.get("center", {}).get("lon")),
                "type": e.get("tags", {}).get("amenity")
                        or e.get("tags", {}).get("shop", "unknown"),
            }
            for e in elements
            if e.get("type") == "node"
        ]

        count = len(competitors)
        # Gap score: 0 competitors → 100, 20+ competitors → ~0
        gap_score = round(max(0, 100 - count * 5), 2)

        return {
            "count": count,
            "competitors": competitors[:20],   # cap list for readability
            "competitor_gap": gap_score,
            "radius_m": radius,
            "explanation": (
                f"Found {count} '{business_type}' competitors within {radius} m. "
                f"Competitor gap score: {gap_score}/100."
            ),
        }

    except Exception as exc:
        logger.error("Overpass API error: %s", exc)
        # Return a neutral mid-score so the rest of the pipeline can continue
        return {
            "count": -1,
            "competitors": [],
            "competitor_gap": 50.0,
            "radius_m": radius,
            "explanation": f"Overpass API error ({exc}). Using neutral gap score 50.",
        }
