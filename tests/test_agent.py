"""
Tests for the LocationScoutAgent and individual tools.
Run with:  pytest tests/ -v
"""

import asyncio
import pytest
import pytest_asyncio

from app.tools.traffic     import get_traffic_score, _synthetic_traffic_score
from app.tools.competitors import get_nearby_competitors, _resolve_osm_types
from app.tools.rent        import get_rent_estimate, _affordability_score
from app.tools.scoring     import score_location
from app.tools.report      import generate_report
from app.agent.agent       import LocationScoutAgent
from app.models.schemas    import ScoutRequest

# Almaty CBD coordinates for all tests
LAT, LNG = 43.2551, 76.9126
ADDRESS   = "Zhibek Zholy Ave 50, Almaly, Almaty"


# ──────────────────────────────────────────────────────────────────────────────
# Traffic tool
# ──────────────────────────────────────────────────────────────────────────────

def test_synthetic_traffic_deterministic():
    s1 = _synthetic_traffic_score(LAT, LNG)
    s2 = _synthetic_traffic_score(LAT, LNG)
    assert s1 == s2, "Synthetic traffic score must be deterministic."

def test_synthetic_traffic_range():
    score = _synthetic_traffic_score(LAT, LNG)
    assert 0 <= score <= 100

@pytest.mark.asyncio
async def test_get_traffic_score_returns_required_keys():
    result = await get_traffic_score(LAT, LNG)
    assert "score"   in result
    assert "source"  in result
    assert 0 <= result["score"] <= 100


# ──────────────────────────────────────────────────────────────────────────────
# Competitors tool
# ──────────────────────────────────────────────────────────────────────────────

def test_resolve_osm_types_coffee():
    types = _resolve_osm_types("coffee shop")
    assert "cafe" in types

def test_resolve_osm_types_unknown():
    types = _resolve_osm_types("pickle_store")
    assert "pickle_store" in types

@pytest.mark.asyncio
async def test_get_nearby_competitors_keys():
    result = await get_nearby_competitors(LAT, LNG, "coffee shop", radius=500)
    assert "count"          in result
    assert "competitor_gap" in result
    assert 0 <= result["competitor_gap"] <= 100


# ──────────────────────────────────────────────────────────────────────────────
# Rent tool
# ──────────────────────────────────────────────────────────────────────────────

def test_affordability_full_budget():
    score = _affordability_score(0, 10_000)
    assert score == 50.0   # zero rent → neutral

def test_affordability_over_budget():
    score = _affordability_score(20_000, 10_000)
    assert score == 0.0

def test_affordability_very_cheap():
    score = _affordability_score(500, 10_000)
    assert score > 90

@pytest.mark.asyncio
async def test_get_rent_estimate_keys():
    result = await get_rent_estimate(ADDRESS, "coffee shop", 10_000)
    assert "avg_rent_kzt"   in result
    assert "rent_affordable" in result
    assert 0 <= result["rent_affordable"] <= 100


# ──────────────────────────────────────────────────────────────────────────────
# Scoring tool
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_score_location_formula():
    factors = {
        "traffic_score":    80,
        "competitor_gap":   60,
        "rent_affordable":  70,
        "demographics_fit": 90,
    }
    result = await score_location(factors)
    expected = 80*0.35 + 60*0.25 + 70*0.20 + 90*0.20
    assert abs(result["final_score"] - expected) < 0.01

@pytest.mark.asyncio
async def test_score_zero_inputs():
    factors = {
        "traffic_score": 0, "competitor_gap": 0,
        "rent_affordable": 0, "demographics_fit": 0,
    }
    result = await score_location(factors)
    assert result["final_score"] == 0.0

@pytest.mark.asyncio
async def test_score_max_inputs():
    factors = {
        "traffic_score": 100, "competitor_gap": 100,
        "rent_affordable": 100, "demographics_fit": 100,
    }
    result = await score_location(factors)
    assert result["final_score"] == 100.0


# ──────────────────────────────────────────────────────────────────────────────
# Report tool
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_report_no_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    # Re-import to pick up monkeypatched env
    import importlib
    import app.tools.report as report_mod
    importlib.reload(report_mod)

    dummy_locations = [
        {
            "id": "loc1", "name": "Test Café", "address": ADDRESS,
            "lat": LAT, "lng": LNG, "district": "Almaly",
            "score_result":  {"final_score": 75, "label": "Good", "breakdown": {}},
            "rent_result":   {"avg_rent_kzt": 3000, "min_rent_kzt": 2500, "max_rent_kzt": 4000},
            "traffic_result":{"score": 70, "source": "synthetic"},
            "competitor_result": {"count": 5, "radius_m": 1000},
        }
    ]
    result = await report_mod.generate_report(dummy_locations)
    assert "report_md" in result
    assert len(result["report_md"]) > 100


# ──────────────────────────────────────────────────────────────────────────────
# Full agent integration
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_returns_top3():
    request = ScoutRequest(
        business_type   = "coffee shop",
        city            = "Almaty",
        budget          = 10_000,
        area_size       = 50,
    )
    agent  = LocationScoutAgent(top_n=3)
    result = await agent.run(request)

    assert 0 < len(result.top_locations) <= 3
    # Scores should be descending
    scores = [loc.final_score for loc in result.top_locations]
    assert scores == sorted(scores, reverse=True)
    assert result.report_md and len(result.report_md) > 50

@pytest.mark.asyncio
async def test_agent_unknown_city_falls_back_to_almaty():
    request = ScoutRequest(
        business_type   = "coffee shop",
        city            = "Narnia",
        budget          = 8_000,
        area_size       = 100,
        top_n           = 2,
    )
    agent  = LocationScoutAgent(top_n=2)
    result = await agent.run(request)
    assert len(result.top_locations) == 2
