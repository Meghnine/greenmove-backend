from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, itineraires, trajets, users
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GreenMove API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(itineraires.router, prefix="/itineraires", tags=["Itineraires"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(trajets.router, prefix="/trajets", tags=["Trajets"])

@app.get("/")
def root():
    return {"message": "GreenMove backend is running ✅"}


