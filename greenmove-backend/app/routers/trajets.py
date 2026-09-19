from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.routers.auth import get_current_user
from app.database import SessionLocal
from app.models.trajet import Trajet
from app.models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TrajetCreate(BaseModel):
    point_depart: Dict[str, Any]
    point_arrivee: Dict[str, Any]
    mode_transport: str
    distance_km: float
    duree_min: float
    co2_kg: float
    route_geojson: Optional[Dict[str, Any]] = None

class TrajetOut(BaseModel):
    id: int
    user_id: int
    point_depart: Dict[str, Any]
    point_arrivee: Dict[str, Any]
    mode_transport: str
    distance_km: float
    duree_min: float
    co2_kg: float
    route_geojson: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True

@router.post("/save", response_model=TrajetOut)
def save_trajet(
    data: TrajetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_trajet = Trajet(
        user_id=current_user.id,
        point_depart=data.point_depart,
        point_arrivee=data.point_arrivee,
        distance_km=data.distance_km,
        duree_min=data.duree_min,
        co2_kg=data.co2_kg,
        mode_transport=data.mode_transport,
        route_geojson=data.route_geojson,
    )

    db.add(new_trajet)
    db.commit()
    db.refresh(new_trajet)
    return new_trajet

@router.get("/history", response_model=List[TrajetOut])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(Trajet)
        .filter(Trajet.user_id == current_user.id)
        .order_by(Trajet.created_at.desc())
        .limit(50)
        .all()
    )
