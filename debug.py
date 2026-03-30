import sys
import traceback
import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agent.agent import LocationScoutAgent, _evaluate_candidate
from app.models.schemas import ScoutRequest

async def main():
    agent = LocationScoutAgent()
    req = ScoutRequest(city="Almaty", business_type="coffee shop", budget=5000000)
    
    try:
        res = await agent.run(req)
        print("Scout run SUCCESS. Top location:", res.top_locations[0].name)
    except Exception as e:
        with open("err.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)

asyncio.run(main())
