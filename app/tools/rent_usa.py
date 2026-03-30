import asyncio
from app.tools.census_data import get_demographics

async def get_rent_estimate(lat: float, lng: float, business_type: str, budget: float, area_size: int = 50) -> dict:
    """
    Returns rent estimation using proxy baseline for commercial rent.
    In real world, commercial is priced per sqft. Here we use an aggressive 2.5x residential multiplier.
    """
    
    demo_data = await get_demographics(lat, lng)
    base_rent = demo_data.get("median_gross_rent_usd", 1500)
    
    # Commercial premium (rough proxy since census is residential)
    # Multiply by area size modifier to give it some variance
    commercial_rent = base_rent * (area_size / 50.0) * 2.8 * 500  # Convert to KZT
    
    # Calculate affordability score (0-100)
    # Ideally rent < 25% of budget. 
    ratio = commercial_rent / budget if budget > 0 else 1
    afford = max(0.0, 100 * (1 - (ratio / 0.5))) # 0 score if rent > 50% of budget
    
    return {
        "avg_rent_kzt": round(commercial_rent),
        "min_rent_kzt": round(commercial_rent * 0.8),
        "max_rent_kzt": round(commercial_rent * 1.3),
        "district": "Local Tract",
        "source": demo_data.get("source", "Proxy Model"),
        "rent_affordable": round(afford, 1),
        "explanation": f"Using base rent proxied for commercial ({area_size} m²). Est: {round(commercial_rent)} 〒/mo. Affordability: {round(afford, 1)}/100."
    }
