from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

import jwt
from app.config import settings

router = APIRouter()

def get_current_user(db: Session = Depends(get_db), token: str = ""):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        return db.query(User).filter(User.email == email).first()
    except:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "nom": user.nom,
        "email": user.email,
        "score_ecologique": user.score_ecologique
    }
