

def get_carbon_estimate(distance_km: float, mode: str) -> float:

    factors = {
        "driving-car": 0.192,
        "cycling-regular": 0.0,
        "foot-walking": 0.0,
        "transit": 0.06,  
    }
    coef = factors.get(mode, 0.192)
    return round(distance_km * coef, 3)
