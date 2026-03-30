"""
API Routes
==========

/health               – liveness probe
/scout                – main agent endpoint (POST)
/tools/traffic        – individual tool: get_traffic_score
/tools/competitors    – individual tool: get_nearby_competitors
/tools/rent           – individual tool: get_rent_estimate
/tools/score          – individual tool: score_location
/candidates           – list all candidate locations for a city

Note: / (root) is handled by app/main.py serving index.html directly.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.agent         import LocationScoutAgent
from app.models        import (
    ScoutRequest, ScoutResult, HealthResponse,
    TrafficRequest, CompetitorRequest, RentRequest, ScoringRequest, KrishaRequest, WorkersRequest
)
from app.tools import (
    get_traffic_score,
    get_nearby_competitors,
    get_rent_estimate,
    score_location,
    scrape_krisha_listings,
)
from app.agent.candidates import ALMATY_CANDIDATES

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton agent (thread-safe; each request creates its own async tasks)
_agent = LocationScoutAgent()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Liveness probe",
)
async def health():
    return HealthResponse()


# ── Main Scout Endpoint ───────────────────────────────────────────────────────

@router.post(
    "/scout",
    response_model=ScoutResult,
    tags=["Scout"],
    summary="Run the full location-scout agent",
    response_description="Top-N ranked locations with scores, ROI estimates, and a narrative report.",
)
async def scout(request: ScoutRequest):
    """
    Evaluates candidate locations for the specified **business_type** and **city**,
    scores each location using a weighted multi-factor model, and returns the
    top locations with a GPT/Claude-generated narrative report.

    - **business_type**: e.g. `"coffee shop"`, `"restaurant"`, `"gym"`
    - **city**: currently supports `"Almaty"` (more cities coming soon)
    - **budget**: monthly operating budget in USD for affordability scoring
    - **target_audience**: demographic profile for demographics-fit scoring
    - **top_n**: how many locations to return (1–10, default 3)
    """
    try:
        agent = LocationScoutAgent(top_n=request.top_n)
        result = await agent.run(request)
        return result
    except Exception as exc:
        logger.exception("Scout agent failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Individual Tool Endpoints ─────────────────────────────────────────────────

@router.post(
    "/tools/traffic",
    tags=["Tools"],
    summary="Get foot-traffic score for a coordinate",
)
async def tool_traffic(req: TrafficRequest):
    """
    Calls Google Maps API (or synthetic fallback) to estimate foot traffic
    at the given `lat`/`lng`.  Returns a 0-100 score.
    """
    try:
        return await get_traffic_score(req.lat, req.lng)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/tools/competitors",
    tags=["Tools"],
    summary="Find nearby competitors via OpenStreetMap",
)
async def tool_competitors(req: CompetitorRequest):
    """
    Queries the Overpass API for `business_type` establishments within
    `radius` metres of `lat`/`lng`.
    """
    try:
        return await get_nearby_competitors(req.lat, req.lng, req.business_type, req.radius)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/tools/rent",
    tags=["Tools"],
    summary="Estimate monthly rent for an address",
)
async def tool_rent(req: RentRequest):
    """
    Estimates commercial rent from a CSV database or a distance-from-CBD
    synthetic model.  Returns avg/min/max rent and an affordability score.
    """
    try:
        return await get_rent_estimate(req.address, req.business_type, req.monthly_budget)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/tools/score",
    tags=["Tools"],
    summary="Score a location from pre-computed sub-scores",
)
async def tool_score(req: ScoringRequest):
    """
    Applies the weighted formula:
    `traffic×0.35 + competitor_gap×0.25 + rent_affordable×0.20 + demographics×0.20`
    """
    try:
        factors = req.model_dump()
        return await score_location(factors)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/tools/krisha",
    tags=["Tools"],
    summary="Scrape real commercial listings from krisha.kz",
)
async def tool_krisha(req: KrishaRequest):
    """
    Scrape real rental listings from krisha.kz for the target city and business type.
    """
    try:
        return await scrape_krisha_listings(req.city, req.business_type, req.limit, req.area_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ── Candidates Listing ────────────────────────────────────────────────────────

@router.post(
    "/tools/workers",
    tags=["Tools"],
    summary="Get candidate workers",
)
async def tool_workers(req: WorkersRequest):
    """
    Get top candidates for a business using Claude.
    """
    try:
        from app.tools.workers import get_workers
        return await get_workers(req.business_type, req.city)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get(
    "/candidates",
    tags=["Scout"],
    summary="List candidate locations for a city",
)
async def candidates(
    city: str = Query(default="Almaty", description="City name"),
):
    """Returns the full list of pre-defined candidate locations for `city`."""
    key = city.lower().strip()
    if key == "almaty":
        return {"city": city, "count": len(ALMATY_CANDIDATES), "candidates": ALMATY_CANDIDATES}
    raise HTTPException(
        status_code=404,
        detail=f"No candidates configured for city '{city}'. Currently supported: Almaty",
    )
