from sqlalchemy import Column, Integer, Float, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Trajet(Base):
    __tablename__ = "trajets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    point_depart = Column(JSON, nullable=True)
    point_arrivee = Column(JSON, nullable=True)

    distance_km = Column(Float, nullable=False)
    duree_min = Column(Float, nullable=False)
    co2_kg = Column(Float, nullable=False)

    mode_transport = Column(String, nullable=False)
    route_geojson = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

