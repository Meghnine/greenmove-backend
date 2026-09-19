from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.ors_service import get_route
from app.services.carbon_service import get_carbon_estimate
from app.services.navitia_service import navitia_journeys

router = APIRouter()


class Coordonnees(BaseModel):
    lat: float
    lon: float

class ItineraireRequest(BaseModel):
    depart: Coordonnees
    arrivee: Coordonnees
    mode: str

class CompareRequest(BaseModel):
    depart: Coordonnees
    arrivee: Coordonnees
    modes: Optional[List[str]] = None  



@router.post("/calc")
async def calc_itineraire(request: ItineraireRequest):
    depart = {"lat": request.depart.lat, "lon": request.depart.lon}
    arrivee = {"lat": request.arrivee.lat, "lon": request.arrivee.lon}

    try:
        route_data = await get_route(depart, arrivee, request.mode)

        distance_km = route_data["distance"] / 1000
        duree_min = route_data["duration"] / 60
        co2_kg = get_carbon_estimate(distance_km, request.mode)

        return {
            "distance_km": round(distance_km, 2),
            "duree_min": round(duree_min, 2),
            "co2_kg": co2_kg,
            "geometry": route_data["geometry"],
        }

    except Exception as e:
        print("ERREUR ITINERAIRE (/calc):", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_itineraires(request: CompareRequest):
    depart = {"lat": request.depart.lat, "lon": request.depart.lon}
    arrivee = {"lat": request.arrivee.lat, "lon": request.arrivee.lon}

    modes = request.modes or ["foot-walking", "cycling-regular", "driving-car", "transit"]

    results = []
    errors = []

    
    from app.services.geo_service import haversine_km
    approx_km = haversine_km(depart["lat"], depart["lon"], arrivee["lat"], arrivee["lon"])

    for mode in modes:
        try:
            if mode == "transit":
                data = await navitia_journeys(depart, arrivee)
                journeys = data.get("journeys", [])
                if not journeys:
                    raise Exception("Aucun trajet transport en commun trouvé")

                
                j = min(journeys, key=lambda x: x.get("duration", 10**9))
                duree_min = round(j.get("duration", 0) / 60, 2)

                
                distance_km = round(approx_km * 1.2, 2)  

                co2_kg = get_carbon_estimate(distance_km, "transit")

                results.append({
                    "mode": "transit",
                    "distance_km": distance_km,
                    "duree_min": duree_min,
                    "co2_kg": co2_kg,
                    "geometry": None,
                    "details": {
                        "nb_transfers": j.get("nb_transfers"),
                        "departure_date_time": j.get("departure_date_time"),
                        "arrival_date_time": j.get("arrival_date_time"),
                    }
                })

            else:
                route_data = await get_route(depart, arrivee, mode)
                distance_km = route_data["distance"] / 1000
                duree_min = route_data["duration"] / 60
                co2_kg = get_carbon_estimate(distance_km, mode)

                results.append({
                    "mode": mode,
                    "distance_km": round(distance_km, 2),
                    "duree_min": round(duree_min, 2),
                    "co2_kg": co2_kg,
                    "geometry": route_data["geometry"],
                })

        except Exception as e:
            errors.append({"mode": mode, "error": str(e)})

    if not results:
        return {"results": [], "recommended": None, "errors": errors}

    

    
    def feasible(r):
        m, t, d = r["mode"], r["duree_min"], r["distance_km"]

    
        if m == "foot-walking" and (t > 60 or d > 6):
            return False

        
        if "cycling" in m and (t > 45 or d > 20):
            return False

        return True

    feasible_results = [r for r in results if feasible(r)]
    if not feasible_results:
        feasible_results = results

    
    co2_min = min(r["co2_kg"] for r in feasible_results)

    
    best_d = min(r["distance_km"] for r in feasible_results if r["distance_km"] is not None)
    if best_d <= 5:
        tol_abs = 0.03  
    elif best_d <= 15:
        tol_abs = 0.15   
    else:
        tol_abs = 0.60   

    limit = co2_min + tol_abs
    eco_candidates = [r for r in feasible_results if r["co2_kg"] <= limit]
    if not eco_candidates:
        eco_candidates = feasible_results


    car = next((r for r in eco_candidates if r["mode"] == "driving-car"), None)
    tr = next((r for r in eco_candidates if r["mode"] == "transit"), None)

    if tr and car:
        if tr["duree_min"] <= car["duree_min"] + 15:
            recommended = tr
        else:
            
            recommended = min(eco_candidates, key=lambda r: r["duree_min"])
    else:
        recommended = min(eco_candidates, key=lambda r: r["duree_min"])


    if best_d <= 5:
        bike = [r for r in eco_candidates if "cycling" in r["mode"]]
        if bike:
            recommended = min(bike, key=lambda r: r["duree_min"])

    return {"results": results, "recommended": recommended, "errors": errors}


    
    for mode in modes:
        try:
        
            if mode == "transit":
                data = await navitia_journeys(depart, arrivee)

                journeys = data.get("journeys", [])
                if not journeys:
                    raise Exception("Aucun trajet transport en commun trouvé")

                j = journeys[0]

            
                duree_min = j.get("duration", 0) / 60

                
                distance_m = 0
                distances = j.get("distances") or {}
                if isinstance(distances, dict):
                    distance_m = (
                        distances.get("walking", 0)
                        + distances.get("bike", 0)
                        + distances.get("car", 0)
                        + distances.get("ridesharing", 0)
                    )

                distance_km = (distance_m / 1000) if distance_m else 0.0

            
                if distance_km > 0:
                    co2_kg = round(distance_km * 0.04, 3)  
                else:
                    co2_kg = round(max(duree_min / 60, 0.5) * 0.04, 3)

                results.append({
                    "mode": "transit",
                    "distance_km": round(distance_km, 2),
                    "duree_min": round(duree_min, 2),
                    "co2_kg": co2_kg,
                    "geometry": None,
                    "details": {
                        "nb_transfers": j.get("nb_transfers"),
                        "departure_date_time": j.get("departure_date_time"),
                        "arrival_date_time": j.get("arrival_date_time"),
                    }
                })

            
            else:
                route_data = await get_route(depart, arrivee, mode)

                distance_km = route_data["distance"] / 1000
                duree_min = route_data["duration"] / 60
                co2_kg = get_carbon_estimate(distance_km, mode)

                results.append({
                    "mode": mode,
                    "distance_km": round(distance_km, 2),
                    "duree_min": round(duree_min, 2),
                    "co2_kg": co2_kg,
                    "geometry": route_data["geometry"],
                })

        except Exception as e:
            errors.append({"mode": mode, "error": str(e)})

    if not results:
        raise HTTPException(
            status_code=500,
            detail={"message": "Aucun itinéraire calculé", "errors": errors}
        )

    
    def is_feasible(r):
        d = r["distance_km"]
        t = r["duree_min"]
        m = r["mode"]

        
        if m == "foot-walking" and (d > 10 or t > 120):
            return False


        if "cycling" in m and (d > 50 or t > 240):
            return False

        return True

    feasible_results = [r for r in results if is_feasible(r)]
    if not feasible_results:
        feasible_results = results

    
    best_distance = min(r["distance_km"] for r in feasible_results)

    threshold_pct = 1.10
    if best_distance <= 5:
        threshold_abs = 0.05
    elif best_distance <= 15:
        threshold_abs = 0.15
    else:
        threshold_abs = 0.60

    
    co2_min = min(r["co2_kg"] for r in feasible_results)
    limit = max(co2_min * threshold_pct, co2_min + threshold_abs)

    eco_candidates = [r for r in feasible_results if r["co2_kg"] <= limit]
    if not eco_candidates:
        eco_candidates = feasible_results

    
    if best_distance <= 5:
        bike_candidates = [r for r in eco_candidates if "cycling" in r["mode"]]
        recommended = min(bike_candidates, key=lambda r: r["duree_min"]) if bike_candidates else min(
            eco_candidates, key=lambda r: r["duree_min"]
        )
    else:
        recommended = min(eco_candidates, key=lambda r: r["duree_min"])

    return {
        "results": results,
        "recommended": recommended,
        "errors": errors
    }
