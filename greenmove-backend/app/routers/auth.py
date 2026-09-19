from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from app.config import settings
from app.database import SessionLocal
from app.models.user import User




router = APIRouter()

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"], 
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "sub": str(user_id),   
        "exp": expire
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")


@router.post("/register")
def register(email: str, password: str, db: Session = Depends(get_db)):
    email = (email or "").strip().lower()
    password = (password or "").strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email requis")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min 6)")

    user_exist = db.query(User).filter(User.email == email).first()
    if user_exist:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    hashed_password = pwd_context.hash(password)  
    new_user = User(email=email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Utilisateur créé avec succès"}

from fastapi.security import OAuth2PasswordRequestForm



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.strip().lower()
    password = form_data.password.strip()

    user_db = db.query(User).filter(User.email == email).first()
    if not user_db or not pwd_context.verify(password, user_db.hashed_password):
        raise HTTPException(status_code=400, detail="Identifiants invalides")

    token = create_token(user_db.id)
    return {"access_token": token, "token_type": "bearer"}



