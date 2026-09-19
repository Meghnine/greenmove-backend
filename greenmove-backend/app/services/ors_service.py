import httpx
from app.config import settings

async def get_route(depart, arrivee, mode):
    url = f"https://api.openrouteservice.org/v2/directions/{mode}"
    headers = {"Authorization": settings.ORS_API_KEY}
    body = {
        "coordinates": [
            [depart["lon"], depart["lat"]],
            [arrivee["lon"], arrivee["lat"]]
        ]
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=body)

    print(" ORS Status:", res.status_code)
    print(" ORS Response:", res.text)

    if res.status_code != 200:
        raise Exception(f"ORS HTTP Error {res.status_code}: {res.text}")

    data = res.json()


    if "routes" not in data:
        raise Exception(f"ORS format error: {data}")

    route = data["routes"][0]
    segment = route["segments"][0]

    return {
        "distance": segment["distance"],
        "duration": segment["duration"],
        "geometry": route.get("geometry")
    }

