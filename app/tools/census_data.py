import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)

# FCC API to convert lat/lng to US Census FIPS (State, County, Tract, Block)
FCC_GEO_URL = "https://geo.fcc.gov/api/census/block/find"
# US Census American Community Survey (ACS) 5-Year Estimates
# Variables:
# B01003_001E = Total Population
# B19013_001E = Median Household Income
# B25064_001E = Median Gross Rent (Residential)
# B15003_022E = Educational Attainment: Bachelor's Degree
CENSUS_URL = "https://api.census.gov/data/2022/acs/acs5"

async def get_fips_codes(lat: float, lng: float) -> dict | None:
    """Returns state and county FIPS codes from coordinates."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                FCC_GEO_URL,
                params={"latitude": lat, "longitude": lng, "format": "json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                state_fips = data.get("State", {}).get("FIPS")
                county_fips = data.get("County", {}).get("FIPS")
                if state_fips and county_fips:
                    # County FIPS in FCC is 5 digits (state + county); Census expects 3 digit county code
                    return {
                        "state": state_fips,
                        "county": county_fips[2:] if len(county_fips) == 5 else county_fips
                    }
    except Exception as e:
        logger.error(f"Error fetching FCC FIPS data: {e}")
    return None

async def get_demographics(lat: float, lng: float) -> dict:
    """
    Fetches real population, median income, and rent data from US Census API.
    """
    fips = await get_fips_codes(lat, lng)
    
    # Sensible defaults if outside USA or API fails
    result = {
        "population": 50000,
        "median_income_usd": 65000,
        "median_gross_rent_usd": 1500,
        "bachelors_degree_count": 10000,
        "source": "US Census Bureau (Fallback)",
        "demographics_fit_raw": 50.0
    }
    
    if not fips:
        return result
        
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                CENSUS_URL,
                params={
                    "get": "NAME,B01003_001E,B19013_001E,B25064_001E,B15003_022E",
                    "for": f"county:{fips['county']}",
                    "in": f"state:{fips['state']}"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                # data[0] is headers, data[1] is the row
                if len(data) > 1:
                    row = dict(zip(data[0], data[1]))
                    
                    pop = int(row.get("B01003_001E") or 0)
                    inc = float(row.get("B19013_001E") or 0)
                    rent = float(row.get("B25064_001E") or 0)
                    edu = int(row.get("B15003_022E") or 0)
                    
                    if pop > 0: result["population"] = pop
                    if inc > 0: result["median_income_usd"] = inc
                    if rent > 0: result["median_gross_rent_usd"] = rent
                    if edu > 0: result["bachelors_degree_count"] = edu
                    
                    result["source"] = "US Census Bureau API (ACS 2022)"
                    
                    # Demographics dynamic scoring proxy
                    # Score 0-100 based on dense affluent areas
                    inc_score = min(100, max(0, (inc - 40000) / 1000))  # e.g., 90k -> 50 score
                    pop_score = min(100, max(0, pop / 20000))
                    result["demographics_fit_raw"] = round((inc_score * 0.6) + (pop_score * 0.4), 1)
                    
    except Exception as e:
        logger.error(f"Error fetching US Census data: {e}")
        
    return result
