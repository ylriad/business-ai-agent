"""
Pydantic schemas for request/response validation.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, model_validator


# ── Request ──────────────────────────────────────────────────────────────────

class ScoutRequest(BaseModel):
    business_type:   str   = Field(
        default="coffee shop",
        description="Type of business to scout locations for.",
        examples=["coffee shop", "restaurant", "gym"],
    )
    city:            str   = Field(
        default="Almaty",
        description="Target city for location scouting.",
    )
    budget:          float = Field(
        default=5_000_000,
        gt=0,
        description="Monthly operating budget in KZT (used for rent-affordability scoring).",
    )
    area_size:       int   = Field(
        default=50,
        description="Desired property area in square meters.",
        examples=[20, 50, 100],
    )
    top_n:           int   = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of top locations to return.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "business_type":   "coffee shop",
                "city":            "Almaty",
                "budget":          5000000,
                "area_size":       50,
                "top_n":           3,
            }
        }
    }


# ── Sub-models ────────────────────────────────────────────────────────────────

class LocationResult(BaseModel):
    id:                  str
    name:                str
    address:             str
    district:            str
    lat:                 float
    lng:                 float
    zone:                str
    krisha_link:         str | None = None
    
    # Scores (0-100)
    final_score:         float
    score_label:         str
    traffic_score:       float
    competitor_gap:      float
    rent_affordable:     float
    demographics_fit:    float

    # Rent
    avg_rent_kzt:        float
    min_rent_kzt:        float
    max_rent_kzt:        float

    # Competitors
    competitor_count:    int
    competitors_nearby:  list[dict[str, Any]] = Field(default_factory=list)

    # Traffic metadata
    traffic_source:      str

    # ROI estimates
    est_monthly_revenue: float
    est_monthly_profit:  float
    est_annual_roi_pct:  float

    # Verbose
    score_explanation:   str


# ── Response ──────────────────────────────────────────────────────────────────

class ScoutResult(BaseModel):
    business_type:    str
    city:             str
    budget:           float
    area_size:        int
    top_locations:    list[LocationResult]
    report_md:        str
    report_source:    str   # 'claude' | 'template' | 'template_fallback'
    total_evaluated:  int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = "1.0.0"
    api:     str = "Location Scout API"


# ── Individual tool request/response pairs (used by /tools/* endpoints) ──────

class TrafficRequest(BaseModel):
    lat: float
    lng: float

class CompetitorRequest(BaseModel):
    lat:           float
    lng:           float
    business_type: str  = "coffee shop"
    radius:        int  = 1000

class RentRequest(BaseModel):
    address:        str
    business_type:  str   = "coffee shop"
    monthly_budget: float = 5_000_000

class ScoringRequest(BaseModel):
    traffic_score:    float = Field(ge=0, le=100)
    competitor_gap:   float = Field(ge=0, le=100)
    rent_affordable:  float = Field(ge=0, le=100)
    demographics_fit: float | None = None
    area_size:        int   = 50
    district:         str   = "Unknown"

class KrishaRequest(BaseModel):
    city:          str = "almaty"
    business_type: str = "coffee shop"
    limit:         int = 5
    area_size:     int = 50

class WorkersRequest(BaseModel):
    city:          str = "Almaty"
    business_type: str = "coffee shop"
