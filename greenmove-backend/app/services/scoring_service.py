def calculate_score(distance_km, co2_kg, duree_min):
    
    score = 100

    score -= co2_kg * 10
    score -= distance_km * 1
    score -= duree_min * 0.2

    if score < 0:
        score = 0
    if score > 100:
        score = 100

    return round(score, 2)
