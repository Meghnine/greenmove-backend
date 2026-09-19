import os
import httpx

NAVITIA_API_KEY = os.getenv("NAVITIA_API_KEY")

NAVITIA_BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

async def navitia_journeys(depart, arrivee):
    if not NAVITIA_API_KEY:
        raise Exception("NAVITIA_API_KEY manquant dans .env")

    url = f"{NAVITIA_BASE_URL}/journeys"

    params = {
        "from": f"{depart['lon']};{depart['lat']}",
        "to": f"{arrivee['lon']};{arrivee['lat']}",
        "datetime_represents": "departure"
    }

    headers = {
        "apiKey": NAVITIA_API_KEY   
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Navitia HTTP {response.status_code}: {response.text}")

        return response.json()
