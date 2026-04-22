import asyncio
from app.agent.agent import _evaluate_candidate

async def main():
    candidate = {
        "id": "test",
        "name": "Test location",
        "lat": 43.2565,
        "lng": 76.9285,
        "rent_kzt": 0, # FORCE IT TO HIT app.tools.rent_usa
        "district": "Medeu"
    }
    
    try:
        res = await _evaluate_candidate(
            candidate=candidate,
            business_type="coffee shop",
            budget=5000000,
            area_size=50
        )
        import pprint
        pprint.pprint(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
